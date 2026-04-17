import React from 'react';
import {useCurrentFrame, interpolate} from 'remotion';

interface FadeTransitionProps {
  durationFrames: number;
  direction: 'in' | 'out';
  color?: string;
}

export const FadeTransition: React.FC<FadeTransitionProps> = ({
  durationFrames,
  direction,
  color = 'black',
}) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(
    frame,
    [0, durationFrames],
    direction === 'in' ? [1, 0] : [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );

  if (opacity === 0) return null;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: color,
        opacity,
        pointerEvents: 'none',
        zIndex: 100,
      }}
    />
  );
};
