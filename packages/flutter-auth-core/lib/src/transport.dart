import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'models.dart';

final class AuthHttpResponse {
  const AuthHttpResponse({
    required this.statusCode,
    required this.headers,
    required this.body,
  });

  final int statusCode;
  final Map<String, String> headers;
  final String body;

  String? header(String name) => headers[name.toLowerCase()];
}

abstract interface class AuthHttpTransport {
  Future<AuthHttpResponse> send(
    Uri uri, {
    required String method,
    Map<String, String>? headers,
    String? body,
    Duration timeout,
  });
}

final class IoAuthHttpTransport implements AuthHttpTransport {
  const IoAuthHttpTransport({this.maxResponseBodyBytes = 64 * 1024});

  final int maxResponseBodyBytes;

  @override
  Future<AuthHttpResponse> send(
    Uri uri, {
    required String method,
    Map<String, String>? headers,
    String? body,
    Duration timeout = const Duration(seconds: 15),
  }) async {
    if (maxResponseBodyBytes < 1024 || maxResponseBodyBytes > 1024 * 1024) {
      throw const AuthTransportException('invalid_transport_configuration');
    }

    final client = HttpClient()..connectionTimeout = timeout;
    try {
      final request = await client.openUrl(method, uri).timeout(timeout);
      request
        ..followRedirects = false
        ..maxRedirects = 0;
      request.headers.set(HttpHeaders.acceptHeader, 'application/json');
      headers?.forEach(request.headers.set);
      if (body != null) {
        request.add(utf8.encode(body));
      }

      final response = await request.close().timeout(timeout);
      final bytes = BytesBuilder(copy: false);
      var totalBytes = 0;
      await for (final chunk in response.timeout(timeout)) {
        totalBytes += chunk.length;
        if (totalBytes > maxResponseBodyBytes) {
          throw const AuthTransportException('response_too_large');
        }
        bytes.add(chunk);
      }

      final responseHeaders = <String, String>{};
      response.headers.forEach((name, values) {
        responseHeaders[name.toLowerCase()] = values.join(',');
      });

      final responseBody = utf8.decode(
        bytes.takeBytes(),
        allowMalformed: false,
      );
      return AuthHttpResponse(
        statusCode: response.statusCode,
        headers: Map.unmodifiable(responseHeaders),
        body: responseBody,
      );
    } on AuthTransportException {
      rethrow;
    } on TimeoutException {
      throw const AuthTransportException('timeout');
    } on FormatException {
      throw const AuthTransportException('invalid_response_encoding');
    } on Object {
      throw const AuthTransportException('network_error');
    } finally {
      client.close(force: true);
    }
  }
}
