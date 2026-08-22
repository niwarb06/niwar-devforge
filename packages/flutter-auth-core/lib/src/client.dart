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

  static final RegExp _publicErrorCodePattern = RegExp(r'[a-z][a-z0-9_]{0,63}');

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
    final existingSession = await _readSession();
    if (existingSession != null) {
      throw const AuthSessionStateException('already_authenticated');
    }

    final response = await _sendJson(
      'auth/session',
      method: 'POST',
      body: <String, Object?>{'identifier': identifier, 'password': password},
    );
    if (response.statusCode != 200) {
      throw _apiException(response);
    }

    final json = _decodeObject(response.body);
    final token = json['session_token'];
    final tokenType = json['token_type'];
    final expiresInSeconds = json['expires_in_seconds'];

    if (token is! String || token.length < 16 || token.trim() != token) {
      throw const InvalidAuthResponse('invalid_session_response');
    }
    if (tokenType != 'bearer' ||
        expiresInSeconds is! int ||
        expiresInSeconds <= 0) {
      await _revokeTokenBestEffort(token);
      throw const InvalidAuthResponse('invalid_session_response');
    }

    final now = DateTime.now().toUtc();
    final expiresIn = Duration(seconds: expiresInSeconds);
    try {
      await _sessionVault.save(token: token, expiresIn: expiresIn, now: now);
    } on Object {
      await _revokeTokenBestEffort(token);
      throw const AuthSessionStorageException('secure_storage_write_failed');
    }

    return MobileLoginResult(
      authenticated: true,
      expiresAt: now.add(expiresIn),
    );
  }

  Future<UserProfile?> currentProfile() async {
    final session = await _readSession();
    if (session == null) return null;

    final response = await _sendJson(
      'users/me',
      method: 'GET',
      authorizationToken: session.token,
    );
    if (response.statusCode == 401) {
      await _clearSession();
      return null;
    }
    if (response.statusCode != 200) {
      throw _apiException(response);
    }
    return _profileFromResponse(response);
  }

  Future<UserProfile> updateProfile({String? displayName}) async {
    final session = await _readSession();
    if (session == null) {
      throw const AuthApiException(statusCode: 401, code: 'not_authenticated');
    }

    final response = await _sendJson(
      'users/me/profile',
      method: 'PATCH',
      authorizationToken: session.token,
      body: <String, Object?>{'display_name': displayName},
    );
    if (response.statusCode == 401) {
      await _clearSession();
      throw const AuthApiException(statusCode: 401, code: 'not_authenticated');
    }
    if (response.statusCode != 200) {
      throw _apiException(response);
    }
    return _profileFromResponse(response);
  }

  Future<LogoutResult> logout() async {
    final session = await _readSession();
    if (session == null) {
      await _clearSession();
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
      await _clearSession();
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

  Future<void> clearLocalSession() => _clearSession();

  Future<StoredSession?> _readSession() async {
    try {
      return await _sessionVault.read();
    } on Object {
      throw const AuthSessionStorageException('secure_storage_read_failed');
    }
  }

  Future<void> _clearSession() async {
    try {
      await _sessionVault.clear();
    } on Object {
      throw const AuthSessionStorageException('secure_storage_clear_failed');
    }
  }

  Future<void> _revokeTokenBestEffort(String token) async {
    try {
      await _sendJson(
        'auth/session',
        method: 'DELETE',
        authorizationToken: token,
      );
    } on Object {
      // The original validation/storage failure remains authoritative. The token
      // is never returned to application state even if cleanup cannot complete.
    }
  }

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
      throw ArgumentError(
        'backendApiBaseUrl must be absolute and include a host',
      );
    }
    if (uri.userInfo.isNotEmpty || uri.hasQuery || uri.hasFragment) {
      throw ArgumentError(
        'backendApiBaseUrl must not include credentials, query, or fragment',
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
        throw ArgumentError(
          'backendApiBaseUrl requires HTTPS outside explicit localhost development',
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

  static bool _isPublicErrorCode(String value) {
    final match = _publicErrorCodePattern.matchAsPrefix(value);
    return match != null && match.end == value.length;
  }

  static AuthApiException _apiException(AuthHttpResponse response) {
    var code = 'request_failed';
    try {
      final json = _decodeObject(response.body);
      final parsedCode = json['code'];
      if (parsedCode is String && _isPublicErrorCode(parsedCode)) {
        code = parsedCode;
      }
    } on Object {
      // Error bodies are intentionally not included in the exception.
    }

    final parsedRetryAfter = int.tryParse(response.header('retry-after') ?? '');
    final retryAfter =
        parsedRetryAfter != null &&
            parsedRetryAfter > 0 &&
            parsedRetryAfter <= 86_400
        ? parsedRetryAfter
        : null;
    return AuthApiException(
      statusCode: response.statusCode,
      code: code,
      retryAfterSeconds: retryAfter,
    );
  }
}
