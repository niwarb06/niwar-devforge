import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:niwar_devforge_flutter_auth/niwar_devforge_flutter_auth.dart';

final class _MemorySecretStore implements SecretStore {
  final Map<String, String> values = <String, String>{};

  @override
  Future<void> write({required String key, required String value}) async {
    values[key] = value;
  }

  @override
  Future<String?> read({required String key}) async => values[key];

  @override
  Future<void> delete({required String key}) async {
    values.remove(key);
  }
}

final class _SequenceTransport implements AuthHttpTransport {
  _SequenceTransport(Iterable<Object> outcomes)
    : _outcomes = List<Object>.of(outcomes);

  final List<Object> _outcomes;

  @override
  Future<AuthHttpResponse> send(
    Uri uri, {
    required String method,
    Map<String, String>? headers,
    String? body,
    Duration timeout = const Duration(seconds: 15),
  }) async {
    if (_outcomes.isEmpty) {
      throw StateError('No transport outcome queued');
    }
    final outcome = _outcomes.removeAt(0);
    if (outcome is AuthHttpResponse) {
      return outcome;
    }
    throw outcome;
  }
}

AuthHttpResponse _jsonResponse(int status, Map<String, Object?> body) {
  return AuthHttpResponse(
    statusCode: status,
    headers: const <String, String>{'content-type': 'application/json'},
    body: jsonEncode(body),
  );
}

SecureSessionVault _memoryVault() => SecureSessionVault(_MemorySecretStore());

void main() {
  test(
    'IO transport applies one deadline to the full request lifecycle',
    () async {
      final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      final subscription = server.listen((request) async {
        try {
          request.response.headers.contentType = ContentType.json;
          for (var index = 0; index < 5; index += 1) {
            request.response.write(' ');
            await request.response.flush();
            await Future<void>.delayed(const Duration(milliseconds: 120));
          }
          request.response.write('{}');
          await request.response.close();
        } on Object {
          // The client intentionally closes the socket when its total deadline wins.
        }
      });

      final transport = IoAuthHttpTransport();
      try {
        await expectLater(
          transport.send(
            Uri.parse('http://${server.address.address}:${server.port}/slow'),
            method: 'GET',
            timeout: const Duration(milliseconds: 250),
          ),
          throwsA(
            isA<AuthTransportException>().having(
              (error) => error.code,
              'code',
              'timeout',
            ),
          ),
        );
      } finally {
        await subscription.cancel();
        await server.close(force: true);
      }
    },
  );

  test(
    'profile network interruption preserves session for resume retry',
    () async {
      const token = 'opaque-resume-session-token-123456789';
      final vault = _memoryVault();
      await vault.save(token: token, expiresIn: const Duration(hours: 1));
      final transport = _SequenceTransport(<Object>[
        const AuthTransportException('network_error'),
        _jsonResponse(200, <String, Object?>{
          'user_id': '4f0b0f44-1498-48bb-93e1-ef898cad9ef6',
          'email': 'resume@example.test',
          'display_name': 'Resume User',
          'is_active': true,
        }),
      ]);
      final client = DevForgeMobileAuthClient(
        backendApiBaseUrl: Uri.parse('https://api.example.test/api/v1'),
        sessionVault: vault,
        transport: transport,
      );

      await expectLater(
        client.currentProfile(),
        throwsA(
          isA<AuthTransportException>().having(
            (error) => error.code,
            'code',
            'network_error',
          ),
        ),
      );
      expect((await vault.read())?.token, token);

      final profile = await client.currentProfile();
      expect(profile?.email, 'resume@example.test');
      expect((await vault.read())?.token, token);
    },
  );

  test(
    'cancellation-style logout failure keeps session for resume retry',
    () async {
      const token = 'opaque-cancelled-logout-session-token-12345';
      final vault = _memoryVault();
      await vault.save(token: token, expiresIn: const Duration(hours: 1));
      final transport = _SequenceTransport(const <Object>[
        AuthTransportException('cancelled'),
        AuthHttpResponse(
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
        client.logout(),
        throwsA(
          isA<AuthTransportException>().having(
            (error) => error.code,
            'code',
            'cancelled',
          ),
        ),
      );
      expect((await vault.read())?.token, token);

      final result = await client.logout();
      expect(result.serverSessionEnded, isTrue);
      expect(await vault.read(), isNull);
    },
  );

  test('login transport timeout never creates a local session', () async {
    final vault = _memoryVault();
    final client = DevForgeMobileAuthClient(
      backendApiBaseUrl: Uri.parse('https://api.example.test/api/v1'),
      sessionVault: vault,
      transport: _SequenceTransport(const <Object>[
        AuthTransportException('timeout'),
      ]),
    );

    await expectLater(
      client.login(identifier: 'user@example.test', password: 'password'),
      throwsA(
        isA<AuthTransportException>().having(
          (error) => error.code,
          'code',
          'timeout',
        ),
      ),
    );
    expect(await vault.read(), isNull);
  });
}
