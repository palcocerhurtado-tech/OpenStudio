import React from 'react';
import {useCurrentFrame, useVideoConfig, interpolate, Easing} from 'remotion';

type KenBurnsMode = 'ken_burns_in' | 'ken_burns_out' | 'parallax_left' | 'parallax_right' | 'static_hold';

interface KenBurnsProps {
  imageSrc: string;
  mode: KenBurnsMode;
  durationFrames: number;
  children?: React.ReactNode;
}

export const KenBurns: React.FC<KenBurnsProps> = ({imageSrc, mode, durationFrames, children}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();

  const progress = interpolate(frame, [0, durationFrames], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.ease),
  });

  let transform = '';
  const overflow = 1.08;

  switch (mode) {
    case 'ken_burns_in':
      transform = `scale(${1 + (overflow - 1) * progress})`;
      break;
    case 'ken_burns_out':
      transform = `scale(${overflow - (overflow - 1) * progress})`;
      break;
    case 'parallax_left':
      transform = `translateX(${-progress * width * 0.04}px) scale(${overflow})`;
      break;
    case 'parallax_right':
      transform = `translateX(${progress * width * 0.04}px) scale(${overflow})`;
      break;
    case 'static_hold':
    default:
      transform = 'scale(1)';
  }

  return (
    <div style={{position: 'relative', width, height, overflow: 'hidden'}}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `url(${imageSrc})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          transform,
          transformOrigin: 'center center',
          willChange: 'transform',
        }}
      />
      {children}
    </div>
  );
};
