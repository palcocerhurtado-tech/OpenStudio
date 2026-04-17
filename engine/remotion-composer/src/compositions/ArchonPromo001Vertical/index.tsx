import React from 'react';
import {AbsoluteFill, Series, Audio, useVideoConfig} from 'remotion';
import {KenBurns} from '../../components/KenBurns';
import {TextOverlay} from '../../components/TextOverlay';
import {SubtitleOverlay} from '../../components/SubtitleOverlay';
import {FadeTransition} from '../../components/SceneTransition';
import type {WordTimestamp} from '../../components/SubtitleOverlay';

// ─── Instagram Reels / TikTok 9:16 variant (1080×1920) ───────────────────────
// Same assets and audio as 16:9. Images are center-cropped and scaled to fill
// the vertical frame. Safe zone: top 10% and bottom 15% reserved for platform UI.

const IMAGES = {
  scene01: '../../../output/archon_promo_001/images/scene_01_problem.png',
  scene02: '../../../output/archon_promo_001/images/scene_02_gap.png',
  scene03: '../../../output/archon_promo_001/images/scene_03_archon.png',
  scene04: '../../../output/archon_promo_001/images/scene_04_documents.png',
  scene05: '../../../output/archon_promo_001/images/scene_05_onboarding.png',
  scene06: '../../../output/archon_promo_001/images/scene_06_reporting.png',
  scene07: '../../../output/archon_promo_001/images/scene_07_trust.png',
  scene08: '../../../output/archon_promo_001/images/scene_08_cta.png',
};

const NARRATION_PATH = '../../../output/archon_promo_001/audio/narration.mp3';
const MUSIC_PATH = '../../../output/archon_promo_001/audio/bg_music.mp3';

const SCENE_DURATIONS = [360, 300, 300, 210, 210, 210, 120, 90];

interface VerticalSceneProps {
  imagePath: string;
  label?: string;
  badge?: string;
  durationFrames: number;
  showBrand?: boolean;
}

const VerticalScene: React.FC<VerticalSceneProps> = ({
  imagePath, label, badge, durationFrames, showBrand,
}) => {
  const {width, height} = useVideoConfig();
  return (
    <AbsoluteFill>
      {/* Image fills vertical frame with center crop */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `url(${imagePath})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center center',
        }}
      />
      <div style={{position: 'absolute', inset: 0, background: 'rgba(5,21,46,0.40)'}} />

      {/* Bottom gradient for text */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: '40%',
          background: 'linear-gradient(to top, rgba(5,21,46,0.90), transparent)',
        }}
      />

      {badge && (
        <div
          style={{
            position: 'absolute',
            bottom: '22%',
            left: 60,
            width: 52,
            height: 52,
            borderRadius: '50%',
            background: '#3E92CC',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 26,
            fontWeight: 700,
            color: '#fff',
            fontFamily: 'Inter, sans-serif',
          }}
        >
          {badge}
        </div>
      )}

      {label && (
        <div
          style={{
            position: 'absolute',
            bottom: '18%',
            left: badge ? 130 : 60,
            right: 60,
            fontFamily: 'Inter, sans-serif',
            fontSize: 38,
            fontWeight: 600,
            color: '#FFFFFF',
            lineHeight: 1.3,
            textShadow: '0 2px 8px rgba(0,0,0,0.5)',
          }}
        >
          {label}
        </div>
      )}

      {showBrand && (
        <div
          style={{
            position: 'absolute',
            bottom: '20%',
            left: 0,
            right: 0,
            textAlign: 'center',
            fontFamily: 'Inter, sans-serif',
          }}
        >
          <div style={{fontSize: 56, fontWeight: 700, color: '#fff', marginBottom: 8}}>
            Archon Consultancies
          </div>
          <div style={{fontSize: 36, fontWeight: 400, color: '#B0C4DE', marginBottom: 16}}>
            Automatización inteligente.
          </div>
          <div style={{fontSize: 34, fontWeight: 600, color: '#3E92CC', letterSpacing: '0.04em'}}>
            archonconsultancies.com
          </div>
        </div>
      )}

      <FadeTransition direction="in" durationFrames={15} />
      <FadeTransition direction="out" durationFrames={15} />
    </AbsoluteFill>
  );
};

export const ArchonPromo001Vertical: React.FC = () => {
  const {fps} = useVideoConfig();
  const wordTimestamps: WordTimestamp[] = [];

  return (
    <AbsoluteFill style={{backgroundColor: '#05152E'}}>
      <Audio src={MUSIC_PATH} volume={(f) => {
        const fadeStart = 52 * fps;
        const fadeEnd = 60 * fps;
        if (f >= fadeStart) return 0.18 * (1 - (f - fadeStart) / (fadeEnd - fadeStart));
        return 0.18;
      }} />
      <Audio src={NARRATION_PATH} volume={1.0} />

      <Series>
        <Series.Sequence durationInFrames={SCENE_DURATIONS[0]}>
          <VerticalScene imagePath={IMAGES.scene01} durationFrames={SCENE_DURATIONS[0]} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={SCENE_DURATIONS[1]}>
          <VerticalScene imagePath={IMAGES.scene02} durationFrames={SCENE_DURATIONS[1]} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={SCENE_DURATIONS[2]}>
          <VerticalScene imagePath={IMAGES.scene03} label="Archon Consultancies · Zaragoza" durationFrames={SCENE_DURATIONS[2]} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={SCENE_DURATIONS[3]}>
          <VerticalScene imagePath={IMAGES.scene04} label="Gestión Documental Automatizada" badge="1" durationFrames={SCENE_DURATIONS[3]} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={SCENE_DURATIONS[4]}>
          <VerticalScene imagePath={IMAGES.scene05} label="Onboarding de Clientes sin Fricciones" badge="2" durationFrames={SCENE_DURATIONS[4]} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={SCENE_DURATIONS[5]}>
          <VerticalScene imagePath={IMAGES.scene06} label="Reporting Inteligente en Tiempo Real" badge="3" durationFrames={SCENE_DURATIONS[5]} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={SCENE_DURATIONS[6]}>
          <VerticalScene imagePath={IMAGES.scene07} durationFrames={SCENE_DURATIONS[6]} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={SCENE_DURATIONS[7]}>
          <VerticalScene imagePath={IMAGES.scene08} durationFrames={SCENE_DURATIONS[7]} showBrand />
        </Series.Sequence>
      </Series>

      <SubtitleOverlay wordTimestamps={wordTimestamps} fps={fps} />
    </AbsoluteFill>
  );
};
