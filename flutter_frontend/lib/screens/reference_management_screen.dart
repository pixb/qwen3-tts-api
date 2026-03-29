import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../theme/app_theme.dart';
import '../widgets/common_widgets.dart';
import '../widgets/audio_player_widget.dart';
import '../models/audio_models.dart';
import '../providers/reference_providers.dart';

// Supported languages
const List<String> supportedLanguages = [
  'Chinese',
  'English',
  'Japanese',
  'Korean',
  'French',
  'German',
  'Spanish',
  'Italian',
  'Portuguese',
  'Russian',
  'Arabic',
  'Hindi',
];

class ReferenceManagementScreen extends ConsumerStatefulWidget {
  const ReferenceManagementScreen({super.key});

  @override
  ConsumerState<ReferenceManagementScreen> createState() =>
      _ReferenceManagementScreenState();
}

class _ReferenceManagementScreenState
    extends ConsumerState<ReferenceManagementScreen> {
  @override
  void initState() {
    super.initState();
    // Load reference audios when the screen is initialized
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(referenceAudioProvider.notifier).loadReferenceAudios();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(referenceAudioProvider);

    ref.listen<ReferenceAudioState>(referenceAudioProvider, (previous, next) {
      if (next.error != null && next.error!.isNotEmpty) {
        _showError(context, next.error!);
        ref.read(referenceAudioProvider.notifier).clearError();
      }
    });

    return Scaffold(
      body: LoadingOverlay(
        isLoading: state.isLoading || state.isUploading,
        message: state.isUploading ? 'Uploading...' : 'Loading...',
        child: SafeArea(
          child: Column(
            children: [
              Expanded(
                child: CustomScrollView(
                  slivers: [
                    SliverToBoxAdapter(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _buildHeader(context, state),
                            const SizedBox(height: 20),
                            _buildUploadCard(context, state),
                            if (state.error != null) ...[
                              const SizedBox(height: 20),
                              _buildErrorMessage(state.error!),
                            ],
                            const SizedBox(height: 20),
                          ],
                        ),
                      ),
                    ),
                    if (state.audios.isEmpty && !state.isLoading)
                      const SliverFillRemaining(
                        child: EmptyState(
                          icon: Icons.library_music_outlined,
                          title: 'No Reference Audios',
                          subtitle:
                              'Upload reference audio files to customize voice style',
                        ),
                      )
                    else
                      SliverPadding(
                        padding: const EdgeInsets.symmetric(horizontal: 24),
                        sliver: SliverList(
                          delegate: SliverChildBuilderDelegate(
                            (context, index) {
                              final audio = state.audios[index];
                              return _buildAudioCard(
                                  context, audio, state.playingAudioId);
                            },
                            childCount: state.audios.length,
                          ),
                        ),
                      ),
                    const SliverToBoxAdapter(
                      child: SizedBox(height: 24),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context, ReferenceAudioState refState) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Reference Audios',
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Manage your reference audio files (${refState.audios.length})',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey.shade600,
              ),
            ),
          ],
        ),
        IconButton(
          onPressed: () {
            ref.read(referenceAudioProvider.notifier).refresh();
          },
          icon: const Icon(Icons.refresh),
          tooltip: 'Refresh',
        ),
      ],
    );
  }

  Widget _buildUploadCard(BuildContext context, ReferenceAudioState state) {
    return GlassCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.secondaryColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.upload_file,
                  color: AppTheme.secondaryColor,
                ),
              ),
              const SizedBox(width: 16),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Upload New',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    SizedBox(height: 4),
                    Text(
                      'Add a reference audio file',
                      style: TextStyle(
                        fontSize: 13,
                        color: AppTheme.textSecondaryLight,
                      ),
                    ),
                  ],
                ),
              ),
              ElevatedButton(
                onPressed: state.isUploading
                    ? null
                    : () =>
                        ref.read(referenceAudioProvider.notifier).pickFile(),
                child: const Text('Select'),
              ),
            ],
          ),
          if (state.selectedFile != null) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.primaryColor.withOpacity(0.05),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  const Icon(Icons.audio_file, color: AppTheme.primaryColor),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      state.selectedFile!.name,
                      style: const TextStyle(fontWeight: FontWeight.w500),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '${(state.selectedFile!.size / 1024).toStringAsFixed(1)} KB',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey.shade600,
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    icon: const Icon(Icons.close, size: 20),
                    onPressed: () => ref
                        .read(referenceAudioProvider.notifier)
                        .clearSelectedFile(),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () => _showUploadDialog(context),
                icon: const Icon(Icons.cloud_upload),
                label: const Text('Upload Audio'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.secondaryColor,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Future<void> _showUploadDialog(BuildContext context) async {
    final state = ref.read(referenceAudioProvider);

    // Form controllers
    final nameController = TextEditingController(
      text: state.selectedFile?.name.replaceAll(RegExp(r'\.[^.]+$'), '') ?? '',
    );
    final refTextController = TextEditingController();
    final instructController = TextEditingController();

    // Form values
    String selectedLanguage = 'Chinese';
    double exaggeration = 0.5;
    double temperature = 0.8;
    double speedRate = 1.0;
    bool isDefault = false;

    final result = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Padding(
          padding: EdgeInsets.only(
            bottom: MediaQuery.of(context).viewInsets.bottom,
          ),
          child: Container(
            decoration: BoxDecoration(
              color: Theme.of(context).scaffoldBackgroundColor,
              borderRadius:
                  const BorderRadius.vertical(top: Radius.circular(24)),
            ),
            padding: const EdgeInsets.all(24),
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(
                    child: Container(
                      width: 40,
                      height: 4,
                      decoration: BoxDecoration(
                        color: Colors.grey.shade300,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'Upload Reference Audio',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Add a reference audio to customize voice style',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey.shade600,
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Selected file display
                  if (state.selectedFile != null)
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppTheme.primaryColor.withOpacity(0.05),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                            color: AppTheme.primaryColor.withOpacity(0.2)),
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: AppTheme.primaryColor.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: const Icon(
                              Icons.audio_file,
                              color: AppTheme.primaryColor,
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  state.selectedFile!.name,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w600,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  '${(state.selectedFile!.size / 1024).toStringAsFixed(1)} KB',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: Colors.grey.shade600,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  const SizedBox(height: 16),

                  // Name field
                  TextField(
                    controller: nameController,
                    decoration: const InputDecoration(
                      labelText: 'Name *',
                      hintText: 'Enter audio name',
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Reference text field (Required)
                  TextField(
                    controller: refTextController,
                    maxLines: 2,
                    decoration: const InputDecoration(
                      labelText: 'Reference Text *',
                      hintText: 'Enter reference text for this audio',
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Language dropdown
                  DropdownButtonFormField<String>(
                    value: selectedLanguage,
                    decoration: const InputDecoration(
                      labelText: 'Language',
                    ),
                    items: supportedLanguages
                        .map((lang) => DropdownMenuItem(
                              value: lang,
                              child: Text(lang),
                            ))
                        .toList(),
                    onChanged: (value) {
                      setState(() {
                        selectedLanguage = value ?? 'Chinese';
                      });
                    },
                  ),
                  const SizedBox(height: 16),

                  // Exaggeration slider
                  _buildSliderField(
                    label: 'Exaggeration',
                    value: exaggeration,
                    min: 0.0,
                    max: 1.0,
                    onChanged: (value) {
                      setState(() {
                        exaggeration = value;
                      });
                    },
                  ),
                  const SizedBox(height: 16),

                  // Temperature slider
                  _buildSliderField(
                    label: 'Temperature',
                    value: temperature,
                    min: 0.0,
                    max: 1.0,
                    onChanged: (value) {
                      setState(() {
                        temperature = value;
                      });
                    },
                  ),
                  const SizedBox(height: 16),

                  // Speed rate slider
                  _buildSliderField(
                    label: 'Speed Rate',
                    value: speedRate,
                    min: 0.5,
                    max: 2.0,
                    onChanged: (value) {
                      setState(() {
                        speedRate = value;
                      });
                    },
                  ),
                  const SizedBox(height: 16),

                  // Instruct field
                  TextField(
                    controller: instructController,
                    maxLines: 2,
                    decoration: const InputDecoration(
                      labelText: 'Voice Style Instruct (Optional)',
                      hintText: 'Enter voice style instructions',
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Set as default switch
                  SwitchListTile(
                    title: const Text('Set as Default'),
                    subtitle:
                        const Text('Use this as the default reference audio'),
                    value: isDefault,
                    onChanged: (value) {
                      setState(() {
                        isDefault = value;
                      });
                    },
                    contentPadding: EdgeInsets.zero,
                  ),
                  const SizedBox(height: 24),

                  // Action buttons
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () => Navigator.pop(context, false),
                          child: const Text('Cancel'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: ElevatedButton(
                          onPressed: () => Navigator.pop(context, true),
                          child: const Text('Upload'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );

    if (result == true) {
      if (nameController.text.trim().isEmpty) {
        _showError(context, 'Please enter a name for the audio');
        return;
      }

      if (refTextController.text.trim().isEmpty) {
        _showError(context, 'Please enter reference text');
        return;
      }

      final notifier = ref.read(referenceAudioProvider.notifier);
      if (notifier.state.selectedFile == null) {
        _showError(context, 'No file selected');
        return;
      }

      print(
          '=================Uploading reference audio: ${nameController.text.trim()}');
      notifier.uploadReferenceAudio(
        name: nameController.text.trim(),
        refText: refTextController.text.trim(),
        language: selectedLanguage,
        exaggeration: exaggeration,
        temperature: temperature,
        instruct: instructController.text.trim(),
        speedRate: speedRate,
        isDefault: isDefault,
      );
      _showSuccess(context, 'Reference audio uploaded successfully!');
    }
  }

  Widget _buildSliderField({
    required String label,
    required double value,
    required double min,
    required double max,
    required ValueChanged<double> onChanged,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: AppTheme.primaryColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                value.toStringAsFixed(2),
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.primaryColor,
                ),
              ),
            ),
          ],
        ),
        Slider(
          value: value,
          min: min,
          max: max,
          onChanged: onChanged,
        ),
      ],
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
            child: Text(
              error,
              style: const TextStyle(
                color: AppTheme.errorColor,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAudioCard(
      BuildContext context, ReferenceAudio audio, String? playingAudioId) {
    final isPlaying = playingAudioId == audio.id;
    final dateFormat = DateFormat('MMM d, yyyy');
    final audioUrl = ref
        .read(referenceAudioProvider.notifier)
        .getReferenceAudioUrl(int.tryParse(audio.id) ?? 0);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isPlaying
              ? AppTheme.primaryColor.withOpacity(0.3)
              : audio.isDefault
                  ? AppTheme.successColor.withOpacity(0.3)
                  : Colors.grey.withOpacity(0.1),
        ),
        boxShadow: isPlaying
            ? [
                BoxShadow(
                  color: AppTheme.primaryColor.withOpacity(0.1),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ]
            : null,
      ),
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                GestureDetector(
                  onTap: () {
                    ref
                        .read(referenceAudioProvider.notifier)
                        .setPlayingAudio(audio.id);
                  },
                  child: Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: isPlaying
                            ? [AppTheme.primaryColor, AppTheme.primaryDark]
                            : audio.isDefault
                                ? [
                                    AppTheme.successColor,
                                    AppTheme.successColor.withGreen(180)
                                  ]
                                : [Colors.grey.shade300, Colors.grey.shade400],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(24),
                    ),
                    child: Icon(
                      isPlaying ? Icons.pause : Icons.play_arrow,
                      color: Colors.white,
                      size: 28,
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              audio.name,
                              style: const TextStyle(
                                fontSize: 15,
                                fontWeight: FontWeight.w600,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          if (audio.isDefault) ...[
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: AppTheme.successColor.withOpacity(0.15),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(
                                    color:
                                        AppTheme.successColor.withOpacity(0.3)),
                              ),
                              child: const Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    Icons.star,
                                    size: 12,
                                    color: AppTheme.successColor,
                                  ),
                                  SizedBox(width: 4),
                                  Text(
                                    'Default',
                                    style: TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.w600,
                                      color: AppTheme.successColor,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ],
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          if (audio.language != null) ...[
                            Icon(
                              Icons.language,
                              size: 14,
                              color: Colors.grey.shade500,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              audio.language!,
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey.shade600,
                              ),
                            ),
                            const SizedBox(width: 12),
                          ],
                          Icon(
                            Icons.schedule,
                            size: 14,
                            color: Colors.grey.shade500,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            dateFormat
                                .format(audio.uploadedAt ?? DateTime.now()),
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey.shade600,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                PopupMenuButton<String>(
                  onSelected: (value) {
                    switch (value) {
                      case 'edit':
                        _showEditDialog(context, audio);
                        break;
                      case 'set_default':
                        final id = int.tryParse(audio.id) ?? 0;
                        ref
                            .read(referenceAudioProvider.notifier)
                            .setDefaultReference(id);
                        _showSuccess(context, 'Set as default reference audio');
                        break;
                      case 'delete':
                        _showDeleteDialog(context, audio);
                        break;
                    }
                  },
                  itemBuilder: (context) => [
                    const PopupMenuItem(
                      value: 'edit',
                      child: Row(
                        children: [
                          Icon(Icons.edit_outlined,
                              color: AppTheme.primaryColor),
                          SizedBox(width: 8),
                          Text('Edit'),
                        ],
                      ),
                    ),
                    if (!audio.isDefault)
                      const PopupMenuItem(
                        value: 'set_default',
                        child: Row(
                          children: [
                            Icon(Icons.star_outline,
                                color: AppTheme.warningColor),
                            SizedBox(width: 8),
                            Text('Set as Default'),
                          ],
                        ),
                      ),
                    const PopupMenuItem(
                      value: 'delete',
                      child: Row(
                        children: [
                          Icon(Icons.delete_outline,
                              color: AppTheme.errorColor),
                          SizedBox(width: 8),
                          Text('Delete',
                              style: TextStyle(color: AppTheme.errorColor)),
                        ],
                      ),
                    ),
                  ],
                  icon: Icon(Icons.more_vert, color: Colors.grey.shade400),
                ),
              ],
            ),
          ),

          // Show parameters if they exist
          if (audio.refText != null ||
              audio.exaggeration != null ||
              audio.temperature != null ||
              audio.speedRate != null ||
              audio.instruct != null)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.only(left: 16, right: 16, bottom: 12),
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  if (audio.refText != null && audio.refText!.isNotEmpty)
                    _buildParameterChip(Icons.text_fields, audio.refText!,
                        maxLines: 2),
                  if (audio.exaggeration != null)
                    _buildParameterChip(Icons.trending_up,
                        'Exag: ${audio.exaggeration!.toStringAsFixed(2)}'),
                  if (audio.temperature != null)
                    _buildParameterChip(Icons.thermostat,
                        'Temp: ${audio.temperature!.toStringAsFixed(2)}'),
                  if (audio.speedRate != null)
                    _buildParameterChip(Icons.speed,
                        'Speed: ${audio.speedRate!.toStringAsFixed(2)}'),
                  if (audio.instruct != null && audio.instruct!.isNotEmpty)
                    _buildParameterChip(
                        Icons.record_voice_over, audio.instruct!,
                        maxLines: 1),
                ],
              ),
            ),

          if (isPlaying)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: AudioPlayerWidget(
                audioUrl: audioUrl,
                autoPlay: true,
                onComplete: () {
                  ref
                      .read(referenceAudioProvider.notifier)
                      .setPlayingAudio(audio.id);
                },
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildParameterChip(IconData icon, String label, {int maxLines = 1}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppTheme.primaryColor.withOpacity(0.08),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: 12,
            color: AppTheme.primaryColor.withOpacity(0.7),
          ),
          const SizedBox(width: 4),
          Flexible(
            child: Text(
              label,
              style: TextStyle(
                fontSize: 11,
                color: AppTheme.primaryColor.withOpacity(0.8),
              ),
              maxLines: maxLines,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _showEditDialog(
      BuildContext context, ReferenceAudio audio) async {
    // Form controllers
    final nameController = TextEditingController(text: audio.name);
    final refTextController = TextEditingController(text: audio.refText ?? '');
    final instructController =
        TextEditingController(text: audio.instruct ?? '');

    // Form values
    String selectedLanguage = audio.language ?? 'Chinese';
    double exaggeration = audio.exaggeration ?? 0.5;
    double temperature = audio.temperature ?? 0.8;
    double speedRate = audio.speedRate ?? 1.0;
    bool isDefault = audio.isDefault;

    final result = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Padding(
          padding: EdgeInsets.only(
            bottom: MediaQuery.of(context).viewInsets.bottom,
          ),
          child: Container(
            constraints: BoxConstraints(
              maxHeight: MediaQuery.of(context).size.height * 0.85,
            ),
            decoration: BoxDecoration(
              color: Theme.of(context).scaffoldBackgroundColor,
              borderRadius:
                  const BorderRadius.vertical(top: Radius.circular(24)),
            ),
            padding: const EdgeInsets.all(24),
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(
                    child: Container(
                      width: 40,
                      height: 4,
                      decoration: BoxDecoration(
                        color: Colors.grey.shade300,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'Upload Reference Audio',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Add a reference audio to customize voice style',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey.shade600,
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Name field
                  TextField(
                    controller: nameController,
                    decoration: const InputDecoration(
                      labelText: 'Name *',
                      hintText: 'Enter audio name',
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Reference text field (Required)
                  TextField(
                    controller: refTextController,
                    maxLines: 2,
                    decoration: const InputDecoration(
                      labelText: 'Reference Text *',
                      hintText: 'Enter reference text for this audio',
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Language dropdown
                  DropdownButtonFormField<String>(
                    value: supportedLanguages.contains(selectedLanguage)
                        ? selectedLanguage
                        : supportedLanguages.first,
                    decoration: const InputDecoration(
                      labelText: 'Language',
                    ),
                    items: supportedLanguages
                        .map((lang) => DropdownMenuItem(
                              value: lang,
                              child: Text(lang),
                            ))
                        .toList(),
                    onChanged: (value) {
                      setState(() {
                        selectedLanguage = value ?? 'Chinese';
                      });
                    },
                  ),
                  const SizedBox(height: 16),

                  // Exaggeration slider
                  _buildSliderField(
                    label: 'Exaggeration',
                    value: exaggeration,
                    min: 0.0,
                    max: 1.0,
                    onChanged: (value) {
                      setState(() {
                        exaggeration = value;
                      });
                    },
                  ),
                  const SizedBox(height: 16),

                  // Temperature slider
                  _buildSliderField(
                    label: 'Temperature',
                    value: temperature,
                    min: 0.0,
                    max: 1.0,
                    onChanged: (value) {
                      setState(() {
                        temperature = value;
                      });
                    },
                  ),
                  const SizedBox(height: 16),

                  // Speed rate slider
                  _buildSliderField(
                    label: 'Speed Rate',
                    value: speedRate,
                    min: 0.5,
                    max: 2.0,
                    onChanged: (value) {
                      setState(() {
                        speedRate = value;
                      });
                    },
                  ),
                  const SizedBox(height: 16),

                  // Instruct field
                  TextField(
                    controller: instructController,
                    maxLines: 2,
                    decoration: const InputDecoration(
                      labelText: 'Voice Style Instruct (Optional)',
                      hintText: 'Enter voice style instructions',
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Set as default switch
                  SwitchListTile(
                    title: const Text('Set as Default'),
                    subtitle:
                        const Text('Use this as the default reference audio'),
                    value: isDefault,
                    onChanged: (value) {
                      setState(() {
                        isDefault = value;
                      });
                    },
                    contentPadding: EdgeInsets.zero,
                  ),
                  const SizedBox(height: 24),

                  // Action buttons
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () => Navigator.pop(context, false),
                          child: const Text('Cancel'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: ElevatedButton(
                          onPressed: () => Navigator.pop(context, true),
                          child: const Text('Save'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );

    if (result == true) {
      if (nameController.text.trim().isEmpty) {
        _showError(context, 'Please enter a name for the audio');
        return;
      }

      if (refTextController.text.trim().isEmpty) {
        _showError(context, 'Please enter reference text');
        return;
      }

      final id = int.tryParse(audio.id) ?? 0;
      ref.read(referenceAudioProvider.notifier).updateReferenceAudio(
            id: id,
            name: nameController.text.trim(),
            refText: refTextController.text.trim(),
            language: selectedLanguage,
            exaggeration: exaggeration,
            temperature: temperature,
            instruct: instructController.text.trim(),
            speedRate: speedRate,
            isDefault: isDefault,
          );
      _showSuccess(context, 'Reference audio updated successfully!');
    }
  }

  Future<void> _showDeleteDialog(
      BuildContext context, ReferenceAudio audio) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Audio'),
        content:
            const Text('Are you sure you want to delete this reference audio?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.errorColor,
            ),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      final id = int.tryParse(audio.id) ?? 0;
      ref.read(referenceAudioProvider.notifier).deleteReferenceAudio(id);
      _showSuccess(context, 'Reference audio deleted successfully!');
    }
  }

  void _showError(BuildContext context, String message) {
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

  void _showSuccess(BuildContext context, String message) {
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
}
