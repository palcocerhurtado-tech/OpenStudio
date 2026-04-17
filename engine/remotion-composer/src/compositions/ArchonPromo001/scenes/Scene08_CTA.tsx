import React from 'react';
import {useCurrentFrame, useVideoConfig, interpolate, spring} from 'remotion';
import {KenBurns} from '../../../components/KenBurns';
import {FadeTransition} from '../../../components/SceneTransition';
import playbook from '../../../../style-playbooks/clean-professional.json';

// Scene 8: "CTA — archonconsultancies.com" — 57s to 60s (frames 1710–1800)
// Full brand moment: logo + tagline + URL on deep navy. Clean and confident.
interface Props {
  imagePath: string;
}

export const Scene08_CTA: React.FC<Props> = ({imagePath}) => {
  const frame = useCurrentFrame();
  const {durationInFrames, fps} = useVideoConfig();

  const brandOpacity = interpolate(frame, [10, 28], [0, 1], {extrapolateRight: 'clamp'});
  const taglineOpacity = interpolate(frame, [22, 40], [0, 1], {extrapolateRight: 'clamp'});
  const urlOpacity = interpolate(frame, [34, 52], [0, 1], {extrapolateRight: 'clamp'});

  const brandY = spring({frame, fps, from: 30, to: 0, config: {damping: 18, stiffness: 100}});
  const taglineY = spring({frame: frame - 12, fps, from: 20, to: 0, config: {damping: 18, stiffness: 100}});
  const urlY = spring({frame: frame - 24, fps, from: 16, to: 0, config: {damping: 18, stiffness: 100}});

  return (
    <div style={{position: 'relative', width: '100%', height: '100%'}}>
      <KenBurns imageSrc={imagePath} mode="static_hold" durationFrames={durationInFrames} />
      {/* Navy overlay — CTA scene lives in brand color space */}
      <div style={{position: 'absolute', inset: 0, background: 'rgba(5,21,46,0.92)'}} />

      {/* Accent bar */}
      <div
        style={{
          position: 'absolute',
          top: '44%',
          left: '50%',
          transform: 'translateX(-50%)',
          width: 56,
          height: 4,
          background: playbook.palette.accent,
          borderRadius: 2,
          opacity: brandOpacity,
        }}
      />

      {/* Brand name */}
      <div
        style={{
          position: 'absolute',
          top: '38%',
          left: '50%',
          transform: `translateX(-50%) translateY(${brandY}px)`,
          opacity: brandOpacity,
          fontFamily: playbook.typography.font_family,
          fontSize: playbook.typography.h1.size,
          fontWeight: playbook.typography.h1.weight,
          color: playbook.palette.text_primary,
          whiteSpace: 'nowrap',
          textAlign: 'center',
        }}
      >
        Archon Consultancies
      </div>

      {/* Tagline */}
      <div
        style={{
          position: 'absolute',
          top: '52%',
          left: '50%',
          transform: `translateX(-50%) translateY(${taglineY}px)`,
          opacity: taglineOpacity,
          fontFamily: playbook.typography.font_family,
          fontSize: playbook.typography.h2.size,
          fontWeight: 400,
          color: playbook.palette.text_secondary,
          whiteSpace: 'nowrap',
          textAlign: 'center',
        }}
      >
        Automatización inteligente.
      </div>

      {/* URL */}
      <div
        style={{
          position: 'absolute',
          top: '63%',
          left: '50%',
          transform: `translateX(-50%) translateY(${urlY}px)`,
          opacity: urlOpacity,
          fontFamily: playbook.typography.font_family,
          fontSize: playbook.typography.cta_url.size,
          fontWeight: playbook.typography.cta_url.weight,
          letterSpacing: playbook.typography.cta_url.letter_spacing,
          color: playbook.palette.accent,
          whiteSpace: 'nowrap',
          textAlign: 'center',
        }}
      >
        archonconsultancies.com
      </div>

      <FadeTransition direction="in" durationFrames={12} />
      {/* Final fade to black */}
      <FadeTransition direction="out" durationFrames={20} />
    </div>
  );
};
