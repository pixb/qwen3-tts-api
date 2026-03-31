import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'api_provider.dart';

class AudioGenerationState {
  final bool isGenerating;
  final bool hasAudio;
  final String? audioUrl;
  final Uint8List? audioBytes;
  final String? error;
  final String? selectedReferenceId;
  final String? selectedReferenceRefText;
  final String? selectedSpeaker;
  final String? voiceInstruct;
  final double exaggeration;
  final double temperature;
  final double speedRate;
  final String? selectedCloneFilePath;
  final Uint8List? selectedCloneFileBytes;
  final String? selectedCloneFileName;
  final String? cloneRefText;
  final String? cloneLanguage;
  final bool isSplitting;
  final List<String> splitChunks;
  final int splitMaxLength;

  const AudioGenerationState({
    this.isGenerating = false,
    this.hasAudio = false,
    this.audioUrl,
    this.audioBytes,
    this.error,
    this.selectedReferenceId,
    this.selectedReferenceRefText,
    this.selectedSpeaker = 'Ryan',
    this.voiceInstruct,
    this.exaggeration = 0.5,
    this.temperature = 0.8,
    this.speedRate = 1.0,
    this.selectedCloneFilePath,
    this.selectedCloneFileBytes,
    this.selectedCloneFileName,
    this.cloneRefText,
    this.cloneLanguage,
    this.isSplitting = false,
    this.splitChunks = const [],
    this.splitMaxLength = 100,
  });

  AudioGenerationState copyWith({
    bool? isGenerating,
    bool? hasAudio,
    String? audioUrl,
    Uint8List? audioBytes,
    String? error,
    String? selectedReferenceId,
    String? selectedReferenceRefText,
    String? selectedSpeaker,
    String? voiceInstruct,
    double? exaggeration,
    double? temperature,
    double? speedRate,
    String? selectedCloneFilePath,
    Uint8List? selectedCloneFileBytes,
    String? selectedCloneFileName,
    String? cloneRefText,
    String? cloneLanguage,
    bool? isSplitting,
    List<String>? splitChunks,
    int? splitMaxLength,
    bool clearAudio = false,
    bool clearError = false,
    bool clearCloneFile = false,
    bool clearSplitChunks = false,
  }) {
    return AudioGenerationState(
      isGenerating: isGenerating ?? this.isGenerating,
      hasAudio: clearAudio ? false : (hasAudio ?? this.hasAudio),
      audioUrl: clearAudio ? null : (audioUrl ?? this.audioUrl),
      audioBytes: clearAudio ? null : (audioBytes ?? this.audioBytes),
      error: clearError ? null : (error ?? this.error),
      selectedReferenceId: selectedReferenceId ?? this.selectedReferenceId,
      selectedReferenceRefText:
          selectedReferenceRefText ?? this.selectedReferenceRefText,
      selectedSpeaker: selectedSpeaker ?? this.selectedSpeaker,
      voiceInstruct: voiceInstruct ?? this.voiceInstruct,
      exaggeration: exaggeration ?? this.exaggeration,
      temperature: temperature ?? this.temperature,
      speedRate: speedRate ?? this.speedRate,
      selectedCloneFilePath: clearCloneFile
          ? null
          : (selectedCloneFilePath ?? this.selectedCloneFilePath),
      selectedCloneFileBytes: clearCloneFile
          ? null
          : (selectedCloneFileBytes ?? this.selectedCloneFileBytes),
      selectedCloneFileName: clearCloneFile
          ? null
          : (selectedCloneFileName ?? this.selectedCloneFileName),
      cloneRefText: cloneRefText ?? this.cloneRefText,
      cloneLanguage: cloneLanguage ?? this.cloneLanguage,
      isSplitting: isSplitting ?? this.isSplitting,
      splitChunks: clearSplitChunks ? [] : (splitChunks ?? this.splitChunks),
      splitMaxLength: splitMaxLength ?? this.splitMaxLength,
    );
  }
}

class AudioGenerationNotifier extends StateNotifier<AudioGenerationState> {
  final DioClient _dioClient;

  AudioGenerationNotifier(this._dioClient)
      : super(const AudioGenerationState());

  void setSelectedReference(String? referenceId, {String? refText}) {
    state = state.copyWith(
      selectedReferenceId: referenceId,
      selectedReferenceRefText: refText,
    );
  }

  void setSelectedSpeaker(String speaker) {
    state = state.copyWith(selectedSpeaker: speaker);
  }

  void setVoiceInstruct(String? instruct) {
    state = state.copyWith(voiceInstruct: instruct);
  }

  void setExaggeration(double value) {
    state = state.copyWith(exaggeration: value);
  }

  void setTemperature(double value) {
    state = state.copyWith(temperature: value);
  }

  void setSpeedRate(double value) {
    state = state.copyWith(speedRate: value);
  }

  void setCloneFile(
      {String? filePath, Uint8List? fileBytes, String? fileName}) {
    state = state.copyWith(
      selectedCloneFilePath: filePath,
      selectedCloneFileBytes: fileBytes,
      selectedCloneFileName: fileName,
    );
  }

  void setCloneRefText(String? refText) {
    state = state.copyWith(cloneRefText: refText);
  }

  void setCloneLanguage(String? language) {
    state = state.copyWith(cloneLanguage: language);
  }

  void setSplitMaxLength(int length) {
    state = state.copyWith(splitMaxLength: length);
  }

  Future<void> splitText(String text) async {
    if (text.trim().isEmpty) {
      state = state.copyWith(error: 'Please enter some text to split');
      return;
    }

    state = state.copyWith(
      isSplitting: true,
      clearSplitChunks: true,
      clearError: true,
    );

    try {
      final response = await _dioClient.post(
        '/text/split',
        data: {
          'text': text.trim(),
          'max_length': state.splitMaxLength,
        },
      );

      if (response.statusCode == 200 && response.data != null) {
        final data = response.data;
        if (data['success'] == true && data['chunks'] != null) {
          final chunks = List<String>.from(data['chunks']);
          state = state.copyWith(
            isSplitting: false,
            splitChunks: chunks,
          );
        } else {
          state = state.copyWith(
            isSplitting: false,
            error: 'Failed to split text',
          );
        }
      } else {
        state = state.copyWith(
          isSplitting: false,
          error: 'Failed to split text',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isSplitting: false,
        error: 'Network error: ${e.toString()}',
      );
    }
  }

  void clearSplitChunks() {
    state = state.copyWith(clearSplitChunks: true);
  }

  Future<void> generateAudioWithReference(String text) async {
    if (text.trim().isEmpty) {
      state = state.copyWith(error: 'Please enter some text to convert');
      return;
    }

    if (state.selectedReferenceId == null ||
        state.selectedReferenceId!.isEmpty) {
      state = state.copyWith(error: 'Please select a reference audio');
      return;
    }

    state = state.copyWith(
      isGenerating: true,
      clearAudio: true,
      clearError: true,
    );

    try {
      final response = await _dioClient.post(
        '/tts/generate',
        data: FormData.fromMap({
          'text': text.trim(),
          'reference_id': int.tryParse(state.selectedReferenceId!) ??
              state.selectedReferenceId,
          'ref_text': state.selectedReferenceRefText ?? '',
          'exaggeration': state.exaggeration,
          'temperature': state.temperature,
          'speed_rate': state.speedRate,
        }),
        options: Options(
          headers: {'Content-Type': 'multipart/form-data'},
          responseType: ResponseType.bytes,
        ),
        timeout: const Duration(minutes: 20),
      );

      if (response.statusCode == 200 && response.data != null) {
        final audioBytes = response.data is List<int>
            ? Uint8List.fromList(response.data as List<int>)
            : null;
        state = state.copyWith(
          isGenerating: false,
          hasAudio: true,
          audioUrl: '/tts/generate',
          audioBytes: audioBytes,
        );
      } else {
        state = state.copyWith(
          isGenerating: false,
          error: 'Failed to generate audio',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isGenerating: false,
        error: 'Network error: ${e.toString()}',
      );
    }
  }

  Future<void> generateCustomVoice(String text) async {
    if (text.trim().isEmpty) {
      state = state.copyWith(error: 'Please enter some text to convert');
      return;
    }

    state = state.copyWith(
      isGenerating: true,
      clearAudio: true,
      clearError: true,
    );

    try {
      final response = await _dioClient.postForm(
        '/tts/custom',
        data: {
          'text': text.trim(),
          'speaker': state.selectedSpeaker,
          'exaggeration': state.exaggeration,
          'temperature': state.temperature,
          'speed_rate': state.speedRate,
          if (state.voiceInstruct != null && state.voiceInstruct!.isNotEmpty)
            'instruct': state.voiceInstruct,
        },
        timeout: const Duration(minutes: 20),
      );

      if (response.statusCode == 200) {
        state = state.copyWith(
          isGenerating: false,
          hasAudio: true,
          audioUrl: '/tts/custom',
        );
      } else {
        state = state.copyWith(
          isGenerating: false,
          error: 'Failed to generate custom voice',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isGenerating: false,
        error: 'Network error: ${e.toString()}',
      );
    }
  }

  Future<void> generateVoiceDesign(String text, String instruct) async {
    if (text.trim().isEmpty) {
      state = state.copyWith(error: 'Please enter some text to convert');
      return;
    }

    if (instruct.trim().isEmpty) {
      state = state.copyWith(error: 'Please enter a voice description');
      return;
    }

    state = state.copyWith(
      isGenerating: true,
      clearAudio: true,
      clearError: true,
    );

    try {
      final response = await _dioClient.postForm(
        '/tts/design',
        data: {
          'text': text.trim(),
          'instruct': instruct.trim(),
          'exaggeration': state.exaggeration,
          'temperature': state.temperature,
          'speed_rate': state.speedRate,
        },
        timeout: const Duration(minutes: 20),
      );

      if (response.statusCode == 200) {
        state = state.copyWith(
          isGenerating: false,
          hasAudio: true,
          audioUrl: '/tts/design',
        );
      } else {
        state = state.copyWith(
          isGenerating: false,
          error: 'Failed to generate voice design',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isGenerating: false,
        error: 'Network error: ${e.toString()}',
      );
    }
  }

  Future<void> generateCloneVoice(String text) async {
    if (text.trim().isEmpty) {
      state = state.copyWith(error: 'Please enter some text to convert');
      return;
    }

    final hasFile = (state.selectedCloneFilePath != null &&
            state.selectedCloneFilePath!.isNotEmpty) ||
        (state.selectedCloneFileBytes != null &&
            state.selectedCloneFileName != null);
    if (!hasFile) {
      state = state.copyWith(error: 'Please select a reference audio file');
      return;
    }

    state = state.copyWith(
      isGenerating: true,
      clearAudio: true,
      clearError: true,
    );

    try {
      MultipartFile audioFile;
      if (kIsWeb) {
        audioFile = MultipartFile.fromBytes(
          state.selectedCloneFileBytes!,
          filename: state.selectedCloneFileName,
        );
      } else {
        audioFile = await MultipartFile.fromFile(state.selectedCloneFilePath!);
      }

      final response = await _dioClient.postMultipart(
        '/tts/clone',
        formData: FormData.fromMap({
          'text': text.trim(),
          'audio_prompt': audioFile,
          if (state.cloneLanguage != null && state.cloneLanguage!.isNotEmpty)
            'language': state.cloneLanguage,
          if (state.cloneRefText != null && state.cloneRefText!.isNotEmpty)
            'ref_text': state.cloneRefText,
          'exaggeration': state.exaggeration,
          'temperature': state.temperature,
          if (state.voiceInstruct != null && state.voiceInstruct!.isNotEmpty)
            'instruct': state.voiceInstruct,
          'speed_rate': state.speedRate,
        }),
        responseType: ResponseType.bytes,
        timeout: const Duration(minutes: 20),
      );

      if (response.statusCode == 200 && response.data != null) {
        final audioBytes = response.data is List<int>
            ? Uint8List.fromList(response.data as List<int>)
            : null;
        state = state.copyWith(
          isGenerating: false,
          hasAudio: true,
          audioUrl: '/tts/clone',
          audioBytes: audioBytes,
        );
      } else {
        state = state.copyWith(
          isGenerating: false,
          error: 'Failed to generate cloned voice',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isGenerating: false,
        error: 'Network error: ${e.toString()}',
      );
    }
  }

  void clearAudio() {
    state = state.copyWith(
        clearAudio: true, clearError: true, clearCloneFile: true);
  }

  void clearError() {
    state = state.copyWith(clearError: true);
  }
}

final audioGenerationProvider =
    StateNotifierProvider<AudioGenerationNotifier, AudioGenerationState>((ref) {
  final dioClient = ref.watch(dioClientProvider);
  return AudioGenerationNotifier(dioClient);
});

class SupportedLanguage {
  final String code;
  final String name;

  SupportedLanguage({required this.code, required this.name});

  factory SupportedLanguage.fromJson(Map<String, dynamic> json) {
    return SupportedLanguage(
      code: json['code'] ?? '',
      name: json['name'] ?? json['code'] ?? '',
    );
  }
}

final languagesProvider = FutureProvider<List<String>>((ref) async {
  final dioClient = ref.watch(dioClientProvider);
  try {
    final response = await dioClient.get('/languages');
    if (response.statusCode == 200) {
      final data = response.data;
      if (data is Map && data['languages'] != null) {
        return List<String>.from(data['languages']);
      }
    }
    return [];
  } catch (e) {
    return [];
  }
});

final healthCheckProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final dioClient = ref.watch(dioClientProvider);
  try {
    final response = await dioClient.get('/health');
    if (response.statusCode == 200) {
      return Map<String, dynamic>.from(response.data);
    }
    return {};
  } catch (e) {
    return {};
  }
});

final presetSpeakersProvider = Provider<List<String>>((ref) {
  return [
    'Ryan',
    'Sarah',
    'Amy',
    'Emma',
    'James',
    'Emily',
    'Oliver',
    'Sophia',
  ];
});
