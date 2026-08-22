final class UserProfile {
  const UserProfile({
    required this.userId,
    required this.email,
    required this.displayName,
    required this.isActive,
  });

  final String userId;
  final String email;
  final String? displayName;
  final bool isActive;

  factory UserProfile.fromJson(Map<String, Object?> json) {
    final userId = json['user_id'];
    final email = json['email'];
    final displayName = json['display_name'];
    final isActive = json['is_active'];

    if (userId is! String || userId.isEmpty) {
      throw const InvalidAuthResponse('invalid_user_id');
    }
    if (email is! String || email.isEmpty) {
      throw const InvalidAuthResponse('invalid_email');
    }
    if (displayName != null && displayName is! String) {
      throw const InvalidAuthResponse('invalid_display_name');
    }
    if (isActive is! bool) {
      throw const InvalidAuthResponse('invalid_is_active');
    }

    return UserProfile(
      userId: userId,
      email: email,
      displayName: displayName as String?,
      isActive: isActive,
    );
  }
}

final class MobileLoginResult {
  const MobileLoginResult({
    required this.authenticated,
    required this.expiresAt,
  });

  final bool authenticated;
  final DateTime expiresAt;

  @override
  String toString() =>
      'MobileLoginResult(authenticated: $authenticated, expiresAt: $expiresAt)';
}

final class LogoutResult {
  const LogoutResult({
    required this.serverSessionEnded,
    required this.wasAlreadySignedOut,
  });

  final bool serverSessionEnded;
  final bool wasAlreadySignedOut;
}

final class AuthApiException implements Exception {
  const AuthApiException({
    required this.statusCode,
    required this.code,
    this.retryAfterSeconds,
  });

  final int statusCode;
  final String code;
  final int? retryAfterSeconds;

  @override
  String toString() => 'AuthApiException(statusCode: $statusCode, code: $code)';
}

final class AuthTransportException implements Exception {
  const AuthTransportException(this.code);

  final String code;

  @override
  String toString() => 'AuthTransportException(code: $code)';
}

final class AuthSessionStateException implements Exception {
  const AuthSessionStateException(this.code);

  final String code;

  @override
  String toString() => 'AuthSessionStateException(code: $code)';
}

final class AuthSessionStorageException implements Exception {
  const AuthSessionStorageException(this.code);

  final String code;

  @override
  String toString() => 'AuthSessionStorageException(code: $code)';
}

final class InvalidAuthResponse implements Exception {
  const InvalidAuthResponse(this.code);

  final String code;

  @override
  String toString() => 'InvalidAuthResponse(code: $code)';
}
