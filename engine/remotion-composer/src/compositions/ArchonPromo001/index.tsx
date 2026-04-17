import React from 'react';
import {AbsoluteFill, Series, Audio, useVideoConfig} from 'remotion';
import {Scene01_Problem} from './scenes/Scene01_Problem';
import {Scene02_Gap} from './scenes/Scene02_Gap';
import {Scene03_Archon} from './scenes/Scene03_Archon';
import {Scene04_Documents} from './scenes/Scene04_Documents';
import {Scene05_Onboarding} from './scenes/Scene05_Onboarding';
import {Scene06_Reporting} from './scenes/Scene06_Reporting';
import {Scene07_Trust} from './scenes/Scene07_Trust';
import {Scene08_CTA} from './scenes/Scene08_CTA';
import {SubtitleOverlay} from '../../components/SubtitleOverlay';
import type {WordTimestamp} from '../../components/SubtitleOverlay';

// ─── Asset paths ──────────────────────────────────────────────────────────────
// These are resolved relative to the output directory at render time.
// The assets pipeline populates these before Remotion render is invoked.

const IMAGES = {
  scene01: '../../output/archon_promo_001/images/scene_01_problem.png',
  scene02: '../../output/archon_promo_001/images/scene_02_gap.png',
  scene03: '../../output/archon_promo_001/images/scene_03_archon.png',
  scene04: '../../output/archon_promo_001/images/scene_04_documents.png',
  scene05: '../../output/archon_promo_001/images/scene_05_onboarding.png',
  scene06: '../../output/archon_promo_001/images/scene_06_reporting.png',
  scene07: '../../output/archon_promo_001/images/scene_07_trust.png',
  scene08: '../../output/archon_promo_001/images/scene_08_cta.png',
};

const NARRATION_PATH = '../../output/archon_promo_001/audio/narration.mp3';
const MUSIC_PATH = '../../output/archon_promo_001/audio/bg_music.mp3';
const WORD_TIMESTAMPS_PATH = '../../output/archon_promo_001/audio/word_timestamps.json';

// ─── Scene durations at 30fps ──────────────────────────────────────────────────
// Total: 60s = 1800 frames
const SCENE_DURATIONS = [360, 300, 300, 210, 210, 210, 120, 90]; // frames

export const ArchonPromo001: React.FC = () => {
  const {fps} = useVideoConfig();

  // Word timestamps are loaded from JSON at render time via staticFile()
  // Fallback to empty array during preview if not yet generated
  const wordTimestamps: WordTimestamp[] = [];

  return (
    <AbsoluteFill style={{backgroundColor: '#05152E'}}>
      {/* Background music — ambient corporate, -18dB */}
      <Audio
        src={MUSIC_PATH}
        volume={(frame) => {
          const fadeOutStart = 52 * fps;
          const fadeOutEnd = 60 * fps;
          if (frame >= fadeOutStart) {
            return 0.18 * (1 - (frame - fadeOutStart) / (fadeOutEnd - fadeOutStart));
          }
          return 0.18;
        }}
      />

      {/* Voiceover narration — 0dB */}
      <Audio src={NARRATION_PATH} volume={1.0} />

      {/* Scene sequence */}
      <Series>
        <Series.Sequence durationInFrames={SCENE_DURATIONS[0]}>
          <Scene01_Problem imagePath={IMAGES.scene01} />
        </Series.Sequence>

        <Series.Sequence durationInFrames={SCENE_DURATIONS[1]}>
          <Scene02_Gap imagePath={IMAGES.scene02} />
        </Series.Sequence>

        <Series.Sequence durationInFrames={SCENE_DURATIONS[2]}>
          <Scene03_Archon imagePath={IMAGES.scene03} />
        </Series.Sequence>

        <Series.Sequence durationInFrames={SCENE_DURATIONS[3]}>
          <Scene04_Documents imagePath={IMAGES.scene04} />
        </Series.Sequence>

        <Series.Sequence durationInFrames={SCENE_DURATIONS[4]}>
          <Scene05_Onboarding imagePath={IMAGES.scene05} />
        </Series.Sequence>

        <Series.Sequence durationInFrames={SCENE_DURATIONS[5]}>
          <Scene06_Reporting imagePath={IMAGES.scene06} />
        </Series.Sequence>

        <Series.Sequence durationInFrames={SCENE_DURATIONS[6]}>
          <Scene07_Trust imagePath={IMAGES.scene07} />
        </Series.Sequence>

        <Series.Sequence durationInFrames={SCENE_DURATIONS[7]}>
          <Scene08_CTA imagePath={IMAGES.scene08} />
        </Series.Sequence>
      </Series>

      {/* Word-level subtitles — rendered on top of all scenes */}
      <SubtitleOverlay wordTimestamps={wordTimestamps} fps={fps} />
    </AbsoluteFill>
  );
};
