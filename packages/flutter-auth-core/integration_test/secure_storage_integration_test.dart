import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:niwar_devforge_flutter_auth/niwar_devforge_flutter_auth.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('platform secure storage persists and clears a session', (
    tester,
  ) async {
    final vault = SecureSessionVault(FlutterSecureStorageSecretStore());
    await vault.clear();
    addTearDown(vault.clear);

    final now = DateTime.utc(2026, 1, 1);
    const token = 'devforge-platform-secure-storage-session-token-1234567890';

    await vault.save(
      token: token,
      expiresIn: const Duration(hours: 1),
      now: now,
    );

    final stored = await vault.read(now: now.add(const Duration(minutes: 5)));
    expect(stored, isNotNull);
    expect(stored!.token, token);
    expect(stored.expiresAt, now.add(const Duration(hours: 1)));

    await vault.clear();
    expect(await vault.read(now: now.add(const Duration(minutes: 10))), isNull);
  });
}
