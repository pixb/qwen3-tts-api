import 'dart:html' as html;
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path_provider/path_provider.dart';
import '../theme/app_theme.dart';
import '../widgets/common_widgets.dart';
import '../widgets/audio_player_widget.dart';
import '../providers/audio_providers.dart';
import '../providers/reference_providers.dart';

enum GenerationMode { reference, clone }

class AudioGenerationScreen extends ConsumerStatefulWidget {
  const AudioGenerationScreen({super.key});

  @override
  ConsumerState<AudioGenerationScreen> createState() =>
      _AudioGenerationScreenState();
}

class _AudioGenerationScreenState extends ConsumerState<AudioGenerationScreen>
    with SingleTickerProviderStateMixin {
  final TextEditingController _textController = TextEditingController();
  final FocusNode _focusNode = FocusNode();
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _textController.dispose();
    _focusNode.dispose();
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final audioState = ref.watch(audioGenerationProvider);
    final referenceState = ref.watch(referenceAudioProvider);

    ref.listen<AudioGenerationState>(audioGenerationProvider, (previous, next) {
      if (next.error != null && next.error!.isNotEmpty) {
        _showError(next.error!);
        ref.read(audioGenerationProvider.notifier).clearError();
      }
      if (next.hasAudio && next.audioUrl != null && (previous?.hasAudio != true)) {
        _showSuccess('Audio generated successfully!');
      }
    });

    return Scaffold(
      body: SafeArea(
        child: LoadingOverlay(
          isLoading: audioState.isGenerating,
          message: 'Generating audio...',
          child: NestedScrollView(
            headerSliverBuilder: (context, innerBoxIsScrolled) {
              return [
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildHeader(),
                        const SizedBox(height: 20),
                        _buildModeTabs(),
                      ],
                    ),
                  ),
                ),
              ];
            },
            body: TabBarView(
              controller: _tabController,
              children: [
                _buildReferenceTab(referenceState),
                _buildCloneTab(),
                _buildLongTextCloneTab(),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Generate Audio',
          style: TextStyle(
            fontSize: 28,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Convert text to natural speech',
          style: TextStyle(
            fontSize: 14,
            color: Colors.grey.shade600,
          ),
        ),
      ],
    );
  }

  Widget _buildModeTabs() {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      decoration: BoxDecoration(
        color: isDark ? Colors.grey.shade900 : Colors.grey.shade100,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isDark ? Colors.grey.shade800 : Colors.grey.shade300,
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: isDark
                ? Colors.black.withOpacity(0.3)
                : Colors.black.withOpacity(0.05),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(14),
        child: TabBar(
          controller: _tabController,
          indicator: BoxDecoration(
            color: AppTheme.primaryColor,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(
              color: AppTheme.primaryLight.withOpacity(0.5),
              width: 1,
            ),
            boxShadow: [
              BoxShadow(
                color: AppTheme.primaryColor.withOpacity(0.4),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          indicatorPadding: const EdgeInsets.all(4),
          indicatorSize: TabBarIndicatorSize.tab,
          labelColor: Colors.white,
          unselectedLabelColor:
              isDark ? Colors.grey.shade400 : Colors.grey.shade700,
          labelStyle: const TextStyle(
            fontWeight: FontWeight.w700,
            fontSize: 13,
            letterSpacing: 0.3,
          ),
          unselectedLabelStyle: TextStyle(
            fontWeight: FontWeight.w500,
            fontSize: 13,
            color: isDark ? Colors.grey.shade500 : Colors.grey.shade600,
          ),
          dividerColor: Colors.transparent,
          splashFactory: NoSplash.splashFactory,
          overlayColor: WidgetStateProperty.resolveWith<Color?>(
            (Set<WidgetState> states) {
              if (states.contains(WidgetState.pressed)) {
                return AppTheme.primaryColor.withOpacity(0.1);
              }
              if (states.contains(WidgetState.hovered)) {
                return AppTheme.primaryColor.withOpacity(0.05);
              }
              return null;
            },
          ),
          tabs: const [
            Tab(
              icon: Icon(Icons.library_music_rounded, size: 20),
              iconMargin: EdgeInsets.only(bottom: 4),
              text: 'Reference',
            ),
            Tab(
              icon: Icon(Icons.content_copy_rounded, size: 20),
              iconMargin: EdgeInsets.only(bottom: 4),
              text: 'Clone',
            ),
            Tab(
              icon: Icon(Icons.notes_rounded, size: 20),
              iconMargin: EdgeInsets.only(bottom: 4),
              text: 'Long Text Clone',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildReferenceTab(ReferenceAudioState referenceState) {
    final audioState = ref.watch(audioGenerationProvider);

    return CustomScrollView(
      slivers: [
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildTextInput(),
                const SizedBox(height: 20),
                _buildReferenceSelector(referenceState),
                const SizedBox(height: 20),
                _buildParameterControls(),
                const SizedBox(height: 20),
                _buildGenerateButton(GenerationMode.reference),
                if (audioState.error != null) ...[
                  const SizedBox(height: 20),
                  _buildErrorMessage(audioState.error!),
                ],
                if (audioState.hasAudio && audioState.audioUrl != null) ...[
                  const SizedBox(height: 24),
                  _buildAudioPlayer(audioState.audioUrl!,
                      audioBytes: audioState.audioBytes),
                ],
                const SizedBox(height: 24),
                _buildTips(),
                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildCloneTab() {
    final audioState = ref.watch(audioGenerationProvider);

    return CustomScrollView(
      slivers: [
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildTextInput(),
                const SizedBox(height: 20),
                _buildCloneAudioSelector(),
                const SizedBox(height: 20),
                _buildCloneRefTextInput(),
                const SizedBox(height: 20),
                _buildVoiceInstructInput(),
                const SizedBox(height: 20),
                _buildParameterControls(),
                const SizedBox(height: 20),
                _buildGenerateButton(GenerationMode.clone),
                if (audioState.error != null) ...[
                  const SizedBox(height: 20),
                  _buildErrorMessage(audioState.error!),
                ],
                if (audioState.hasAudio && audioState.audioUrl != null) ...[
                  const SizedBox(height: 24),
                  _buildAudioPlayer(audioState.audioUrl!,
                      audioBytes: audioState.audioBytes),
                ],
                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildLongTextCloneTab() {
    final audioState = ref.watch(audioGenerationProvider);

    return CustomScrollView(
      slivers: [
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildTextInput(),
                const SizedBox(height: 20),
                _buildSplitControls(),
                const SizedBox(height: 20),
                if (audioState.splitChunks.isNotEmpty) ...[
                  _buildSplitChunksList(),
                  const SizedBox(height: 20),
                ],
                _buildCloneAudioSelector(),
                const SizedBox(height: 20),
                _buildCloneRefTextInput(),
                const SizedBox(height: 20),
                _buildVoiceInstructInput(),
                const SizedBox(height: 20),
                _buildParameterControls(),
                const SizedBox(height: 20),
                _buildGenerateButton(GenerationMode.clone),
                if (audioState.error != null) ...[
                  const SizedBox(height: 20),
                  _buildErrorMessage(audioState.error!),
                ],
                if (audioState.hasAudio && audioState.audioUrl != null) ...[
                  const SizedBox(height: 24),
                  _buildAudioPlayer(audioState.audioUrl!,
                      audioBytes: audioState.audioBytes),
                ],
                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSplitControls() {
    final audioState = ref.watch(audioGenerationProvider);

    return GlassCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Text Splitting',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          Text(
            'Split long text into smaller chunks for processing',
            style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Max Length: ${audioState.splitMaxLength}',
                      style:
                          TextStyle(fontSize: 13, color: Colors.grey.shade600),
                    ),
                    Slider(
                      value: audioState.splitMaxLength.toDouble(),
                      min: 50,
                      max: 500,
                      divisions: 9,
                      onChanged: (value) {
                        ref
                            .read(audioGenerationProvider.notifier)
                            .setSplitMaxLength(value.toInt());
                      },
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 16),
              ElevatedButton.icon(
                onPressed: audioState.isSplitting
                    ? null
                    : () {
                        ref
                            .read(audioGenerationProvider.notifier)
                            .splitText(_textController.text);
                      },
                icon: audioState.isSplitting
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.content_cut, size: 18),
                label: Text(audioState.isSplitting ? 'Splitting...' : 'Split'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSplitChunksList() {
    final audioState = ref.watch(audioGenerationProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Split Chunks (${audioState.splitChunks.length})',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            TextButton.icon(
              onPressed: () {
                ref.read(audioGenerationProvider.notifier).clearSplitChunks();
              },
              icon: const Icon(Icons.clear, size: 18),
              label: const Text('Clear'),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(
            color: Theme.of(context).cardColor,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.grey.withOpacity(0.1)),
          ),
          child: ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: audioState.splitChunks.length,
            separatorBuilder: (context, index) => Divider(
              height: 1,
              color: Colors.grey.withOpacity(0.2),
            ),
            itemBuilder: (context, index) {
              final chunk = audioState.splitChunks[index];
              return ListTile(
                leading: CircleAvatar(
                  backgroundColor: AppTheme.primaryColor.withOpacity(0.1),
                  child: Text(
                    '${index + 1}',
                    style: const TextStyle(
                      color: AppTheme.primaryColor,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                title: Text(
                  chunk,
                  style: const TextStyle(fontSize: 14),
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
                subtitle: Text(
                  '${chunk.length} characters',
                  style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                ),
                trailing: IconButton(
                  icon: const Icon(Icons.copy, size: 18),
                  onPressed: () {
                    // Copy to clipboard functionality could be added here
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content:
                            Text('Chunk ${index + 1} copied to text input'),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                    _textController.text = chunk;
                  },
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildCloneAudioSelector() {
    final audioState = ref.watch(audioGenerationProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Reference Audio File',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 8),
        Text(
          'Select an audio file to clone voice from',
          style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
        ),
        const SizedBox(height: 12),
        GlassCard(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Icon(
                audioState.selectedCloneFilePath != null ||
                        audioState.selectedCloneFileName != null
                    ? Icons.audio_file
                    : Icons.upload_file,
                size: 40,
                color: audioState.selectedCloneFilePath != null ||
                        audioState.selectedCloneFileName != null
                    ? AppTheme.primaryColor
                    : Colors.grey,
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      audioState.selectedCloneFilePath != null ||
                              audioState.selectedCloneFileName != null
                          ? (audioState.selectedCloneFilePath
                                  ?.split('/')
                                  .last ??
                              audioState.selectedCloneFileName ??
                              '')
                          : 'No file selected',
                      style: const TextStyle(
                        fontWeight: FontWeight.w500,
                        fontSize: 14,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (audioState.selectedCloneFilePath != null)
                      Text(
                        audioState.selectedCloneFilePath!,
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey.shade600,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                  ],
                ),
              ),
              OutlinedButton(
                onPressed: () => _pickCloneAudioFile(),
                child: Text(audioState.selectedCloneFilePath != null ||
                        audioState.selectedCloneFileName != null
                    ? 'Change'
                    : 'Select'),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildCloneRefTextInput() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Reference Text *',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 8),
        Text(
          'Text that corresponds to the reference audio',
          style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
        ),
        const SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(
            color: Theme.of(context).cardColor,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.grey.withOpacity(0.1)),
          ),
          child: TextField(
            onChanged: (value) {
              ref.read(audioGenerationProvider.notifier).setCloneRefText(value);
            },
            maxLines: 3,
            decoration: InputDecoration(
              hintText: 'Enter the text spoken in the reference audio...',
              hintStyle: TextStyle(color: Colors.grey.shade400),
              border: InputBorder.none,
              contentPadding: const EdgeInsets.all(16),
            ),
            style: const TextStyle(fontSize: 15),
          ),
        ),
      ],
    );
  }

  Widget _buildVoiceInstructInput() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Voice Instruct (Optional)',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 8),
        Text(
          'Additional instructions for voice generation',
          style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
        ),
        const SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(
            color: Theme.of(context).cardColor,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.grey.withOpacity(0.1)),
          ),
          child: TextField(
            onChanged: (value) {
              ref
                  .read(audioGenerationProvider.notifier)
                  .setVoiceInstruct(value);
            },
            maxLines: 2,
            decoration: InputDecoration(
              hintText:
                  'Enter voice instructions (e.g., speak slowly, whisper)...',
              hintStyle: TextStyle(color: Colors.grey.shade400),
              border: InputBorder.none,
              contentPadding: const EdgeInsets.all(16),
            ),
            style: const TextStyle(fontSize: 15),
          ),
        ),
      ],
    );
  }

  Future<void> _pickCloneAudioFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.audio,
      allowMultiple: false,
    );

    if (result != null && result.files.isNotEmpty) {
      final file = result.files.first;
      if (kIsWeb) {
        ref.read(audioGenerationProvider.notifier).setCloneFile(
              fileBytes: file.bytes,
              fileName: file.name,
            );
      } else {
        ref.read(audioGenerationProvider.notifier).setCloneFile(
              filePath: file.path,
            );
      }
    }
  }

  Widget _buildTextInput() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Text Input',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            if (_textController.text.isNotEmpty)
              TextButton.icon(
                onPressed: _clearText,
                icon: const Icon(Icons.clear, size: 18),
                label: const Text('Clear'),
                style: TextButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                ),
              ),
          ],
        ),
        const SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(
            color: Theme.of(context).cardColor,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.grey.withOpacity(0.1)),
          ),
          child: TextField(
            controller: _textController,
            focusNode: _focusNode,
            maxLines: 6,
            minLines: 4,
            onChanged: (value) => setState(() {}),
            decoration: InputDecoration(
              hintText: 'Enter the text you want to convert to speech...',
              hintStyle: TextStyle(color: Colors.grey.shade400, height: 1.5),
              border: InputBorder.none,
              contentPadding: const EdgeInsets.all(16),
              counterText: '${_textController.text.length} characters',
            ),
            style: const TextStyle(fontSize: 15, height: 1.6),
          ),
        ),
      ],
    );
  }

  Widget _buildReferenceSelector(ReferenceAudioState referenceState) {
    final audioState = ref.watch(audioGenerationProvider);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Reference Audio',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 12),
        if (referenceState.isLoading)
          const Center(child: CircularProgressIndicator(strokeWidth: 2))
        else if (referenceState.audios.isEmpty)
          _buildEmptyReferenceHint()
        else
          SizedBox(
            height: 48,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: referenceState.audios.length + 1,
              itemBuilder: (context, index) {
                if (index == 0) {
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: const Text('None'),
                      selected: audioState.selectedReferenceId == null,
                      onSelected: (selected) {
                        if (selected) {
                          ref
                              .read(audioGenerationProvider.notifier)
                              .setSelectedReference(null);
                        }
                      },
                      selectedColor: AppTheme.primaryColor.withOpacity(0.2),
                    ),
                  );
                }
                final audio = referenceState.audios[index - 1];
                final isSelected = audioState.selectedReferenceId == audio.id;
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ChoiceChip(
                    label: Text(audio.name),
                    selected: isSelected,
                    onSelected: (selected) {
                      if (selected) {
                        ref
                            .read(audioGenerationProvider.notifier)
                            .setSelectedReference(audio.id,
                                refText: audio.refText);
                      }
                    },
                    selectedColor: AppTheme.primaryColor.withOpacity(0.2),
                    avatar: isSelected
                        ? const Icon(Icons.check,
                            size: 18, color: AppTheme.primaryColor)
                        : const Icon(Icons.audiotrack,
                            size: 18, color: Colors.grey),
                  ),
                );
              },
            ),
          ),
      ],
    );
  }

  Widget _buildEmptyReferenceHint() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Row(
        children: [
          Icon(Icons.info_outline, color: Colors.grey.shade500, size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              'No reference audios. Upload in References tab.',
              style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildParameterControls() {
    final audioState = ref.watch(audioGenerationProvider);

    return GlassCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Parameters',
            style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 16),
          _buildSlider('Exaggeration', audioState.exaggeration, (v) {
            ref.read(audioGenerationProvider.notifier).setExaggeration(v);
          }),
          _buildSlider('Temperature', audioState.temperature, (v) {
            ref.read(audioGenerationProvider.notifier).setTemperature(v);
          }),
          _buildSlider('Speed', audioState.speedRate, (v) {
            ref.read(audioGenerationProvider.notifier).setSpeedRate(v);
          }, min: 0.5, max: 2.0),
        ],
      ),
    );
  }

  Widget _buildSlider(
      String label, double value, ValueChanged<double> onChanged,
      {double min = 0.0, double max = 1.0}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label,
                style: TextStyle(fontSize: 13, color: Colors.grey.shade600)),
            Text(value.toStringAsFixed(2),
                style:
                    const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
          ],
        ),
        SliderTheme(
          data: SliderTheme.of(context).copyWith(trackHeight: 4),
          child: Slider(
            value: value,
            min: min,
            max: max,
            onChanged: onChanged,
          ),
        ),
      ],
    );
  }

  Widget _buildGenerateButton(GenerationMode mode) {
    final audioState = ref.watch(audioGenerationProvider);
    final cloneRefText = audioState.cloneRefText;

    bool canGenerate = _textController.text.trim().isNotEmpty;
    if (mode == GenerationMode.clone) {
      canGenerate =
          canGenerate && (cloneRefText != null && cloneRefText.isNotEmpty);
    }

    return GradientButton(
      text: 'Generate Audio',
      icon: Icons.mic,
      onPressed: canGenerate
          ? () {
              if (mode == GenerationMode.clone &&
                  (cloneRefText == null || cloneRefText.isEmpty)) {
                _showError('Please enter reference text');
                return;
              }
              switch (mode) {
                case GenerationMode.reference:
                  ref
                      .read(audioGenerationProvider.notifier)
                      .generateAudioWithReference(_textController.text);
                  break;
                case GenerationMode.clone:
                  ref
                      .read(audioGenerationProvider.notifier)
                      .generateCloneVoice(_textController.text);
                  break;
              }
            }
          : null,
      isLoading: audioState.isGenerating,
      width: double.infinity,
    );
  }

  Widget _buildErrorMessage(String error) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.errorColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.errorColor.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline, color: AppTheme.errorColor),
          const SizedBox(width: 12),
          Expanded(
            child: Text(error,
                style: const TextStyle(
                    color: AppTheme.errorColor, fontWeight: FontWeight.w500)),
          ),
        ],
      ),
    );
  }

  Widget _buildAudioPlayer(String audioUrl, {Uint8List? audioBytes}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SectionHeader(title: 'Generated Audio'),
        AudioPlayerWidget(
            audioUrl: audioUrl, audioBytes: audioBytes, autoPlay: false),
        const SizedBox(height: 12),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            OutlinedButton.icon(
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                      content: Text('Audio URL: $audioUrl'),
                      behavior: SnackBarBehavior.floating),
                );
              },
              icon: const Icon(Icons.share, size: 18),
              label: const Text('Share'),
            ),
            const SizedBox(width: 12),
            OutlinedButton.icon(
              onPressed: () => _downloadAudio(audioBytes),
              icon: const Icon(Icons.download, size: 18),
              label: const Text('Download'),
            ),
            const SizedBox(width: 12),
            OutlinedButton.icon(
              onPressed: _clearText,
              icon: const Icon(Icons.refresh, size: 18),
              label: const Text('New'),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildTips() {
    return GlassCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.lightbulb_outline,
                  color: Colors.amber.shade700, size: 20),
              const SizedBox(width: 8),
              const Text('Tips',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
            ],
          ),
          const SizedBox(height: 12),
          _buildTipItem('Use proper punctuation for natural pauses'),
          _buildTipItem('Keep text under 1000 characters for best quality'),
          _buildTipItem('Select a reference audio for voice style matching'),
        ],
      ),
    );
  }

  Widget _buildTipItem(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.check_circle,
              color: AppTheme.successColor, size: 16),
          const SizedBox(width: 8),
          Expanded(
              child: Text(text,
                  style: TextStyle(fontSize: 13, color: Colors.grey.shade700))),
        ],
      ),
    );
  }

  void _clearText() {
    _textController.clear();
    ref.read(audioGenerationProvider.notifier).clearAudio();
    setState(() {});
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.error_outline, color: Colors.white, size: 20),
            const SizedBox(width: 12),
            Expanded(child: Text(message)),
          ],
        ),
        backgroundColor: AppTheme.errorColor,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }

  void _showSuccess(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.check_circle, color: Colors.white, size: 20),
            const SizedBox(width: 12),
            Text(message),
          ],
        ),
        backgroundColor: AppTheme.successColor,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }

  Future<void> _downloadAudio(Uint8List? audioBytes) async {
    if (audioBytes == null) {
      _showError('No audio data available for download');
      return;
    }

    try {
      if (kIsWeb) {
        // For web platform
        final blob = html.Blob([audioBytes], 'audio/wav');
        final url = html.Url.createObjectUrlFromBlob(blob);
        final anchor = html.AnchorElement(href: url)
          ..setAttribute('download', 'generated_audio.wav')
          ..click();
        html.Url.revokeObjectUrl(url);
        _showSuccess('Audio downloaded successfully!');
      } else {
        // For mobile platforms
        final directory = await getDownloadsDirectory();
        if (directory == null) {
          _showError('No downloads directory available');
          return;
        }
        final file = File('${directory.path}/generated_audio.wav');
        await file.writeAsBytes(audioBytes);
        _showSuccess('Audio downloaded to ${file.path}');
      }
    } catch (e) {
      _showError('Failed to download audio: ${e.toString()}');
    }
  }
}
