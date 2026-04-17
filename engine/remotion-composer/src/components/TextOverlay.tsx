import React from 'react';
import {useCurrentFrame, interpolate, spring, useVideoConfig} from 'remotion';
import playbook from '../../style-playbooks/clean-professional.json';

export type TextStyle = 'h1' | 'h2' | 'body_large' | 'body' | 'cta_url' | 'subtitle';
export type TextPosition = 'center' | 'lower-third' | 'center-up' | 'center-down' | 'lower-center';

interface TextOverlayProps {
  text: string;
  style: TextStyle;
  position: TextPosition;
  inFrame: number;
  outFrame: number;
}

const POSITIONS: Record<TextPosition, React.CSSProperties> = {
  'center':       {top: '50%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center'},
  'center-up':    {top: '40%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center'},
  'center-down':  {top: '62%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center'},
  'lower-third':  {bottom: '18%', left: 80, right: 80, textAlign: 'left'},
  'lower-center': {bottom: '20%', left: '50%', transform: 'translateX(-50%)', textAlign: 'center', whiteSpace: 'nowrap'},
};

export const TextOverlay: React.FC<TextOverlayProps> = ({text, style, position, inFrame, outFrame}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const typo = playbook.typography[style] ?? playbook.typography.body;

  const opacity = interpolate(
    frame,
    [inFrame, inFrame + 10, outFrame - 8, outFrame],
    [0, 1, 1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );

  const translateY = spring({
    frame: frame - inFrame,
    fps,
    config: {damping: 18, stiffness: 120, mass: 0.8},
    from: 20,
    to: 0,
  });

  if (frame < inFrame || frame > outFrame) return null;

  return (
    <div
      style={{
        position: 'absolute',
        ...POSITIONS[position],
        opacity,
        transform: `${POSITIONS[position].transform ?? ''} translateY(${translateY}px)`,
        fontFamily: playbook.typography.font_family,
        fontSize: typo.size,
        fontWeight: typo.weight,
        lineHeight: typo.line_height,
        letterSpacing: (typo as any).letter_spacing ?? 0,
        color: playbook.palette.text_primary,
        textShadow: '0 2px 12px rgba(0,0,0,0.6)',
        padding: '6px 16px',
        zIndex: 10,
        maxWidth: '80%',
      }}
    >
      {text}
    </div>
  );
};
