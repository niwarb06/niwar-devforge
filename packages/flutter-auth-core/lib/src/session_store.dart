import 'package:flutter_secure_storage/flutter_secure_storage.dart';

abstract interface class SecretStore {
  Future<void> write({required String key, required String value});

  Future<String?> read({required String key});

  Future<void> delete({required String key});
}

final class FlutterSecureStorageSecretStore implements SecretStore {
  FlutterSecureStorageSecretStore({FlutterSecureStorage? storage})
    : _storage = storage ?? FlutterSecureStorage();

  final FlutterSecureStorage _storage;

  @override
  Future<void> write({required String key, required String value}) =>
      _storage.write(key: key, value: value);

  @override
  Future<String?> read({required String key}) => _storage.read(key: key);

  @override
  Future<void> delete({required String key}) => _storage.delete(key: key);
}

final class StoredSession {
  const StoredSession({required this.token, required this.expiresAt});

  final String token;
  final DateTime expiresAt;
}

final class SecureSessionVault {
  SecureSessionVault(this._store);

  static const _tokenKey = 'devforge.auth.session.token.v1';
  static const _expiresAtKey = 'devforge.auth.session.expires_at_ms.v1';

  final SecretStore _store;

  Future<void> save({
    required String token,
    required Duration expiresIn,
    DateTime? now,
  }) async {
    if (token.length < 16 || token.trim() != token) {
      throw ArgumentError.value(token.length, 'token', 'invalid session token');
    }
    if (expiresIn <= Duration.zero) {
      throw ArgumentError.value(expiresIn, 'expiresIn', 'must be positive');
    }

    final baseTime = (now ?? DateTime.now()).toUtc();
    final expiresAt = baseTime.add(expiresIn);

    await clear();
    await _store.write(
      key: _expiresAtKey,
      value: expiresAt.millisecondsSinceEpoch.toString(),
    );
    try {
      await _store.write(key: _tokenKey, value: token);
    } on Object {
      await _store.delete(key: _expiresAtKey);
      rethrow;
    }
  }

  Future<StoredSession?> read({DateTime? now}) async {
    final token = await _store.read(key: _tokenKey);
    final expiresAtRaw = await _store.read(key: _expiresAtKey);
    if (token == null || expiresAtRaw == null) {
      await clear();
      return null;
    }

    final expiresAtMs = int.tryParse(expiresAtRaw);
    if (token.length < 16 || token.trim() != token || expiresAtMs == null) {
      await clear();
      return null;
    }

    final expiresAt = DateTime.fromMillisecondsSinceEpoch(expiresAtMs, isUtc: true);
    final currentTime = (now ?? DateTime.now()).toUtc();
    if (!expiresAt.isAfter(currentTime)) {
      await clear();
      return null;
    }

    return StoredSession(token: token, expiresAt: expiresAt);
  }

  Future<void> clear() async {
    await _store.delete(key: _tokenKey);
    await _store.delete(key: _expiresAtKey);
  }
}
