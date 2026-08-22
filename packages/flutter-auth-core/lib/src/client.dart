import 'dart:convert';

import 'models.dart';
import 'session_store.dart';
import 'transport.dart';

final class DevForgeMobileAuthClient {
  DevForgeMobileAuthClient({
    required Uri backendApiBaseUrl,
    required SecureSessionVault sessionVault,
    AuthHttpTransport? transport,
    this.requestTimeout = const Duration(seconds: 15),
    bool allowInsecureLocalhostForDevelopment = false,
  }) : _baseUrl = _normalizeBaseUrl(
         backendApiBaseUrl,
         allowInsecureLocalhostForDevelopment:
             allowInsecureLocalhostForDevelopment,
       ),
       _sessionVault = sessionVault,
       _transport = transport ?? const IoAuthHttpTransport();

  final Uri _baseUrl;
  final SecureSessionVault _sessionVault;
  final AuthHttpTransport _transport;
  final Duration requestTimeout;

  Future<UserProfile> register({
    required String email,
    required String password,
    String? displayName,
  }) async {
    final response = await _sendJson(
      'auth/register',
      method: 'POST',
      body: <String, Object?>{
        'email': email,
        'password': password,
        'display_name': displayName,
      },
    );
    if (response.statusCode != 201) {
      throw _apiException(response);
    }
    return _profileFromResponse(response);
  }

  Future<MobileLoginResult> login({
    required String identifier,
    required String password,
  }) async {
    final response = await _sendJson(
      'auth/session',
      method: 'POST',
      body: <String, Object?>{
        'identifier': identifier,
        'password': password,
      },
    );
    if (response.statusCode != 200) {
      throw _apiException(response);
    }

    final json = _decodeObject(response.body);
    final token = json['session_token'];
    final tokenType = json['token_type'];
    final expiresInSeconds = json['expires_in_seconds'];
    if (
      token is! String ||
      token.length < 16 ||
      tokenType != 'bearer' ||
      expiresInSeconds is! int ||
      expiresInSeconds <= 0
    ) {
      throw const InvalidAuthResponse('invalid_session_response');
    }

    final now = DateTime.now().toUtc();
    final expiresIn = Duration(seconds: expiresInSeconds);
    await _sessionVault.save(token: token, expiresIn: expiresIn, now: now);
    return MobileLoginResult(
      authenticated: true,
      expiresAt: now.add(expiresIn),
    );
  }

  Future<UserProfile?> currentProfile() async {
    final session = await _sessionVault.read();
    if (session == null) return null;

    final response = await _sendJson(
      'users/me',
      method: 'GET',
      authorizationToken: session.token,
    );
    if (response.statusCode == 401) {
      await _sessionVault.clear();
      return null;
    }
    if (response.statusCode != 200) {
      throw _apiException(response);
    }
    return _profileFromResponse(response);
  }

  Future<UserProfile> updateProfile({String? displayName}) async {
    final session = await _sessionVault.read();
    if (session == null) {
      throw const AuthApiException(
        statusCode: 401,
        code: 'not_authenticated',
      );
    }

    final response = await _sendJson(
      'users/me/profile',
      method: 'PATCH',
      authorizationToken: session.token,
      body: <String, Object?>{'display_name': displayName},
    );
    if (response.statusCode == 401) {
      await _sessionVault.clear();
      throw const AuthApiException(
        statusCode: 401,
        code: 'not_authenticated',
      );
    }
    if (response.statusCode != 200) {
      throw _apiException(response);
    }
    return _profileFromResponse(response);
  }

  Future<LogoutResult> logout() async {
    final session = await _sessionVault.read();
    if (session == null) {
      await _sessionVault.clear();
      return const LogoutResult(
        serverSessionEnded: true,
        wasAlreadySignedOut: true,
      );
    }

    final response = await _sendJson(
      'auth/session',
      method: 'DELETE',
      authorizationToken: session.token,
    );
    if (response.statusCode == 204 || response.statusCode == 401) {
      await _sessionVault.clear();
      return const LogoutResult(
        serverSessionEnded: true,
        wasAlreadySignedOut: false,
      );
    }

    // Keep the secure local credential on transient/unknown server failure so
    // the caller can retry server-side revocation instead of silently orphaning
    // an active session. Call clearLocalSession() only for an explicit local reset.
    throw _apiException(response);
  }

  Future<void> clearLocalSession() => _sessionVault.clear();

  Future<AuthHttpResponse> _sendJson(
    String path, {
    required String method,
    Map<String, Object?>? body,
    String? authorizationToken,
  }) {
    final headers = <String, String>{};
    if (body != null) {
      headers['Content-Type'] = 'application/json; charset=utf-8';
    }
    if (authorizationToken != null) {
      headers['Authorization'] = 'Bearer $authorizationToken';
    }

    return _transport.send(
      _baseUrl.resolve(path),
      method: method,
      headers: headers,
      body: body == null ? null : jsonEncode(body),
      timeout: requestTimeout,
    );
  }

  static Uri _normalizeBaseUrl(
    Uri uri, {
    required bool allowInsecureLocalhostForDevelopment,
  }) {
    if (!uri.isAbsolute || uri.host.isEmpty) {
      throw ArgumentError.value(uri, 'backendApiBaseUrl', 'must be absolute');
    }
    if (uri.userInfo.isNotEmpty || uri.hasQuery || uri.hasFragment) {
      throw ArgumentError.value(
        uri,
        'backendApiBaseUrl',
        'must not include credentials, query, or fragment',
      );
    }

    final scheme = uri.scheme.toLowerCase();
    final host = uri.host.toLowerCase();
    final isLoopback =
        host == 'localhost' || host == '127.0.0.1' || host == '::1';
    if (scheme != 'https') {
      final localDevelopmentException =
          scheme == 'http' &&
          isLoopback &&
          allowInsecureLocalhostForDevelopment;
      if (!localDevelopmentException) {
        throw ArgumentError.value(
          uri,
          'backendApiBaseUrl',
          'HTTPS is required outside explicit localhost development',
        );
      }
    }

    final path = uri.path.endsWith('/') ? uri.path : '${uri.path}/';
    return uri.replace(path: path);
  }

  static UserProfile _profileFromResponse(AuthHttpResponse response) {
    try {
      return UserProfile.fromJson(_decodeObject(response.body));
    } on InvalidAuthResponse {
      rethrow;
    } on Object {
      throw const InvalidAuthResponse('invalid_profile_response');
    }
  }

  static Map<String, Object?> _decodeObject(String body) {
    final Object? decoded;
    try {
      decoded = jsonDecode(body);
    } on FormatException {
      throw const InvalidAuthResponse('invalid_json_response');
    }
    if (decoded is! Map<String, dynamic>) {
      throw const InvalidAuthResponse('invalid_json_object');
    }
    return Map<String, Object?>.from(decoded);
  }

  static AuthApiException _apiException(AuthHttpResponse response) {
    var code = 'request_failed';
    try {
      final json = _decodeObject(response.body);
      final parsedCode = json['code'];
      if (parsedCode is String && parsedCode.isNotEmpty) {
        code = parsedCode;
      }
    } on Object {
      // Error bodies are intentionally not included in the exception.
    }

    final retryAfter = int.tryParse(response.header('retry-after') ?? '');
    return AuthApiException(
      statusCode: response.statusCode,
      code: code,
      retryAfterSeconds: retryAfter,
    );
  }
}
