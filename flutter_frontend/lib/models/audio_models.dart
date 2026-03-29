class AudioGenerationRequest {
  final String text;
  final String? referenceAudioId;
  final Map<String, dynamic>? options;

  AudioGenerationRequest({
    required this.text,
    this.referenceAudioId,
    this.options,
  });

  Map<String, dynamic> toJson() {
    return {
      'text': text,
      if (referenceAudioId != null) 'reference_id': referenceAudioId,
      if (options != null) ...options!,
    };
  }
}

class AudioGenerationResponse {
  final String? id;
  final String status;
  final String? audioUrl;
  final String? errorMessage;
  final DateTime? createdAt;

  AudioGenerationResponse({
    this.id,
    required this.status,
    this.audioUrl,
    this.errorMessage,
    this.createdAt,
  });

  factory AudioGenerationResponse.fromJson(Map<String, dynamic> json) {
    return AudioGenerationResponse(
      id: json['id']?.toString(),
      status: json['status'] ?? 'pending',
      audioUrl: json['audio_url'],
      errorMessage: json['error_message'] ?? json['detail'],
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'])
          : DateTime.now(),
    );
  }
}

class ReferenceAudio {
  final String id;
  final String name;
  final String? url;
  final int? duration;
  final DateTime? uploadedAt;
  final String? filePath;
  final String? refText;
  final String? language;
  final double? exaggeration;
  final double? temperature;
  final String? instruct;
  final double? speedRate;
  final bool isDefault;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  ReferenceAudio({
    required this.id,
    required this.name,
    this.url,
    this.duration,
    this.uploadedAt,
    this.filePath,
    this.refText,
    this.language,
    this.exaggeration,
    this.temperature,
    this.instruct,
    this.speedRate,
    this.isDefault = false,
    this.createdAt,
    this.updatedAt,
  });

  factory ReferenceAudio.fromJson(Map<String, dynamic> json) {
    return ReferenceAudio(
      id: json['id']?.toString() ?? '',
      name: json['name'] ?? 'Unknown',
      url: json['url'],
      duration: json['duration'] ?? json['file_duration'],
      uploadedAt: json['uploaded_at'] != null
          ? DateTime.tryParse(json['uploaded_at'])
          : json['created_at'] != null
              ? DateTime.tryParse(json['created_at'])
              : json['updated_at'] != null
                  ? DateTime.tryParse(json['updated_at'])
                  : DateTime.now(),
      filePath: json['file_path'],
      refText: json['ref_text'],
      language: json['language'],
      exaggeration: json['exaggeration']?.toDouble(),
      temperature: json['temperature']?.toDouble(),
      instruct: json['instruct'],
      speedRate: json['speed_rate']?.toDouble(),
      isDefault: json['is_default'] == true || json['is_default'] == 1,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'])
          : null,
      updatedAt: json['updated_at'] != null
          ? DateTime.tryParse(json['updated_at'])
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      if (url != null) 'url': url,
      if (duration != null) 'duration': duration,
      if (uploadedAt != null) 'uploaded_at': uploadedAt!.toIso8601String(),
      if (filePath != null) 'file_path': filePath,
      if (refText != null) 'ref_text': refText,
      if (language != null) 'language': language,
      if (exaggeration != null) 'exaggeration': exaggeration,
      if (temperature != null) 'temperature': temperature,
      if (instruct != null) 'instruct': instruct,
      if (speedRate != null) 'speed_rate': speedRate,
      'is_default': isDefault,
      if (createdAt != null) 'created_at': createdAt!.toIso8601String(),
      if (updatedAt != null) 'updated_at': updatedAt!.toIso8601String(),
    };
  }

  ReferenceAudio copyWith({
    String? id,
    String? name,
    String? url,
    int? duration,
    DateTime? uploadedAt,
    String? filePath,
    String? refText,
    String? language,
    double? exaggeration,
    double? temperature,
    String? instruct,
    double? speedRate,
    bool? isDefault,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return ReferenceAudio(
      id: id ?? this.id,
      name: name ?? this.name,
      url: url ?? this.url,
      duration: duration ?? this.duration,
      uploadedAt: uploadedAt ?? this.uploadedAt,
      filePath: filePath ?? this.filePath,
      refText: refText ?? this.refText,
      language: language ?? this.language,
      exaggeration: exaggeration ?? this.exaggeration,
      temperature: temperature ?? this.temperature,
      instruct: instruct ?? this.instruct,
      speedRate: speedRate ?? this.speedRate,
      isDefault: isDefault ?? this.isDefault,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}

class AudioGenerationHistory {
  final String id;
  final String text;
  final String? audioUrl;
  final String status;
  final DateTime createdAt;
  final String? referenceAudioId;

  AudioGenerationHistory({
    required this.id,
    required this.text,
    this.audioUrl,
    required this.status,
    required this.createdAt,
    this.referenceAudioId,
  });

  factory AudioGenerationHistory.fromJson(Map<String, dynamic> json) {
    return AudioGenerationHistory(
      id: json['id'] ?? '',
      text: json['text'] ?? '',
      audioUrl: json['audio_url'],
      status: json['status'] ?? 'pending',
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : DateTime.now(),
      referenceAudioId: json['reference_audio_id']?.toString(),
    );
  }
}
