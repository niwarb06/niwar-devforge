import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:niwar_devforge_flutter_auth/niwar_devforge_flutter_auth.dart';

final class MemorySecretStore implements SecretStore {
  MemorySecretStore({this.failWrites = false});

  final bool failWrites;
  final Map<String, String> values = <String, String>{};

  @override
  Future<void> write({required String key, required String value}) async {
    if (failWrites) {
      throw StateError('simulated secure storage failure');
    }
    values[key] = value;
  }

  @override
  Future<String?> read({required String key}) async => values[key];

  @override
  Future<void> delete({required String key}) async {
    values.remove(key);
  }
}

final class RecordedRequest {
  const RecordedRequest({
    required this.uri,
    required this.method,
    required this.headers,
    required this.body,
  });

  final Uri uri;
  final String method;
  final Map<String, String> headers;
  final String? body;
}

final class QueueTransport implements AuthHttpTransport {
  QueueTransport(List<AuthHttpResponse> responses)
    : _responses = List<AuthHttpResponse>.of(responses);

  final List<AuthHttpResponse> _responses;
  final List<RecordedRequest> requests = <RecordedRequest>[];

  @override
  Future<AuthHttpResponse> send(
    Uri uri, {
    required String method,
    Map<String, String>? headers,
    String? body,
    Duration timeout = const Duration(seconds: 15),
  }) async {
    requests.add(
      RecordedRequest(
        uri: uri,
        method: method,
        headers: Map<String, String>.unmodifiable(
          headers ?? const <String, String>{},
        ),
        body: body,
      ),
    );
    if (_responses.isEmpty) {
      throw StateError('No fake response queued');
    }
    return _responses.removeAt(0);
  }
}

AuthHttpResponse jsonResponse(int status, Map<String, Object?> body) {
  return AuthHttpResponse(
    statusCode: status,
    headers: const <String, String>{'content-type': 'application/json'},
    body: jsonEncode(body),
  );
}

SecureSessionVault memoryVault() => SecureSessionVault(MemorySecretStore());

void main() {
  test(
    'login stores opaque token in the vault but does not expose it in result',
    () async {
      const token = 'opaque-mobile-session-token-123456789';
      final vault = memoryVault();
      final transport = QueueTransport(<AuthHttpResponse>[
        jsonResponse(200, <String, Object?>{
          'session_token': token,
          'token_type': 'bearer',
          'expires_in_seconds': 3600,
        }),
      ]);
      final client = DevForgeMobileAuthClient(
        backendApiBaseUrl: Uri.parse('https://api.example.test/api/v1'),
        sessionVault: vault,
        transport: transport,
      );

      final result = await client.login(
        identifier: 'user@example.test',
        password: 'correct-horse-battery-staple',
      );

      expect(result.authenticated, isTrue);
      expect(result.toString(), isNot(contains(token)));
      expect((await vault.read())?.token, token);
      expect(transport.requests.single.uri.path, '/api/v1/auth/session');
    },
  );

  test('login refuses to replace an already active local session', () async {
    final vault = memoryVault();
    await vault.save(
      token: 'opaque-existing-session-token-123456',
      expiresIn: const Duration(hours: 1),
    );
    final transport = QueueTransport(const <AuthHttpResponse>[]);
    final client = DevForgeMobileAuthClient(
      backendApiBaseUrl: Uri.parse('https://api.example.test/api/v1'),
      sessionVault: vault,
      transport: transport,
    );

    await expectLater(
      client.login(identifier: 'other@example.test', password: 'password'),
      throwsA(
        isA<AuthSessionStateException>().having(
          (error) => error.code,
          'code',
          'already_authenticated',
        ),
      ),
    );
    expect(transport.requests, isEmpty);
  });

  test('failed secure persistence attempts immediate server revocation', () async {
    const token = 'opaque-new-session-token-storage-fail-123';
    final vault = SecureSessionVault(MemorySecretStore(failWrites: true));
    final transport = QueueTransport(<AuthHttpResponse>[
      jsonResponse(200, <String, Object?>{
        'session_token': token,
        'token_type': 'bearer',
        'expires_in_seconds': 3600,
      }),
      const AuthHttpResponse(
        statusCode: 204,
        headers: <String, String>{},
        body: '',
      ),
    ]);
    final client = DevForgeMobileAuthClient(
      backendApiBaseUrl: Uri.parse('https://api.example.test/api/v1'),
      sessionVault: vault,
      transport: transport,
    );

    await expectLater(
      client.login(identifier: 'user@example.test', password: 'password'),
      throwsA(
        isA<AuthSessionStorageException>().having(
          (error) => error.code,
          'code',
          'secure_storage_write_failed',
        ),
      ),
    );

    expect(transport.requests, hasLength(2));
    expect(transport.requests.last.method, 'DELETE');
    expect(transport.requests.last.uri.path, '/api/v1/auth/session');
    expect(transport.requests.last.headers['Authorization'], 'Bearer $token');
  });

  test(
    'authenticated profile reads translate secure token to bearer server call',
    () async {
      const token = 'opaque-mobile-session-token-abcdefghi';
      final vault = memoryVault();
      await vault.save(token: token, expiresIn: const Duration(hours: 1));
      final transport = QueueTransport(<AuthHttpResponse>[
        jsonResponse(200, <String, Object?>{
          'user_id': '2f4191c8-d1d9-4b16-bc22-1cad431b7ae2',
          'email': 'user@example.test',
          'display_name': 'Mobile User',
          'is_active': true,
        }),
      ]);
      final client = DevForgeMobileAuthClient(
        backendApiBaseUrl: Uri.parse('https://api.example.test/api/v1'),
        sessionVault: vault,
        transport: transport,
      );

      final profile = await client.currentProfile();

      expect(profile?.email, 'user@example.test');
      expect(
        transport.requests.single.headers['Authorization'],
        'Bearer $token',
      );
    },
  );

  test('401 clears stale secure session', () async {
    const token = 'opaque-mobile-session-token-stale-123';
    final vault = memoryVault();
    await vault.save(token: token, expiresIn: const Duration(hours: 1));
    final transport = QueueTransport(<AuthHttpResponse>[
      jsonResponse(401, <String, Object?>{
        'code': 'not_authenticated',
        'message': null,
      }),
    ]);
    final client = DevForgeMobileAuthClient(
      backendApiBaseUrl: Uri.parse('https://api.example.test/api/v1'),
      sessionVault: vault,
      transport: transport,
    );

    expect(await client.currentProfile(), isNull);
    expect(await vault.read(), isNull);
  });

  test('expired secure session is deleted before it can be reused', () async {
    final store = MemorySecretStore();
    final vault = SecureSessionVault(store);
    final now = DateTime.utc(2026, 8, 22, 8);
    await vault.save(
      token: 'opaque-mobile-session-token-expired-123',
      expiresIn: const Duration(seconds: 5),
      now: now,
    );

    final session = await vault.read(now: now.add(const Duration(seconds: 6)));

    expect(session, isNull);
    expect(store.values, isEmpty);
  });

  test(
    'registration returns profile and never creates a local session',
    () async {
      final vault = memoryVault();
      final transport = QueueTransport(<AuthHttpResponse>[
        jsonResponse(201, <String, Object?>{
          'user_id': '4a335073-e9dc-416f-b133-836fe7cf1a68',
          'email': 'new@example.test',
          'display_name': null,
          'is_active': true,
        }),
      ]);
      final client = DevForgeMobileAuthClient(
        backendApiBaseUrl: Uri.parse('https://api.example.test/api/v1'),
        sessionVault: vault,
        transport: transport,
      );

      final profile = await client.register(
        email: 'new@example.test',
        password: 'correct-horse-battery-staple',
      );

      expect(profile.email, 'new@example.test');
      expect(await vault.read(), isNull);
    },
  );

  test(
    'malformed login success is rejected before token persistence',
    () async {
      final vault = memoryVault();
      final transport = QueueTransport(<AuthHttpResponse>[
        jsonResponse(200, <String, Object?>{
          'session_token': 'short',
          'token_type': 'bearer',
          'expires_in_seconds': 3600,
        }),
      ]);
      final client = DevForgeMobileAuthClient(
        backendApiBaseUrl: Uri.parse('https://api.example.test/api/v1'),
        sessionVault: vault,
        transport: transport,
      );

      await expectLater(
        client.login(identifier: 'user@example.test', password: 'password'),
        throwsA(isA<InvalidAuthResponse>()),
      );
      expect(await vault.read(), isNull);
    },
  );

  test(
    'logout keeps local token when server revocation cannot be confirmed',
    () async {
      const token = 'opaque-mobile-session-token-retry-12345';
      final vault = memoryVault();
      await vault.save(token: token, expiresIn: const Duration(hours: 1));
      final transport = QueueTransport(<AuthHttpResponse>[
        jsonResponse(503, <String, Object?>{
          'code': 'temporarily_unavailable',
          'message': null,
        }),
      ]);
      final client = DevForgeMobileAuthClient(
        backendApiBaseUrl: Uri.parse('https://api.example.test/api/v1'),
        sessionVault: vault,
        transport: transport,
      );

      await expectLater(client.logout(), throwsA(isA<AuthApiException>()));
      expect((await vault.read())?.token, token);
    },
  );

  test(
    'production transport requires HTTPS and only permits explicit localhost HTTP',
    () {
      expect(
        () => DevForgeMobileAuthClient(
          backendApiBaseUrl: Uri.parse('http://api.example.test/api/v1'),
          sessionVault: memoryVault(),
        ),
        throwsArgumentError,
      );

      final localClient = DevForgeMobileAuthClient(
        backendApiBaseUrl: Uri.parse('http://127.0.0.1:8000/api/v1'),
        sessionVault: memoryVault(),
        allowInsecureLocalhostForDevelopment: true,
      );
      expect(localClient, isA<DevForgeMobileAuthClient>());
    },
  );

  test('API exceptions do not echo upstream error bodies or credentials', () {
    const error = AuthApiException(
      statusCode: 401,
      code: 'invalid_credentials',
    );
    expect(
      error.toString(),
      'AuthApiException(statusCode: 401, code: invalid_credentials)',
    );
    expect(error.toString(), isNot(contains('password')));
  });
}
