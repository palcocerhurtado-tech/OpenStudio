import React from 'react';
import {useCurrentFrame} from 'remotion';
import playbook from '../../style-playbooks/clean-professional.json';

export interface WordTimestamp {
  word: string;
  start_s: number;
  end_s: number;
}

interface SubtitleOverlayProps {
  wordTimestamps: WordTimestamp[];
  fps: number;
}

export const SubtitleOverlay: React.FC<SubtitleOverlayProps> = ({wordTimestamps, fps}) => {
  const frame = useCurrentFrame();
  const currentTime = frame / fps;

  const activeWords = wordTimestamps.filter(
    (w) => currentTime >= w.start_s && currentTime <= w.end_s + 0.15,
  );

  const subtitleStyle = playbook.subtitles;

  if (activeWords.length === 0) return null;

  // Group into lines of max 42 chars
  const words: string[] = [];
  let charCount = 0;
  const lines: string[][] = [[]];

  for (const w of wordTimestamps.filter(
    (w) => currentTime >= w.start_s - 0.05 && currentTime < w.start_s + 3,
  )) {
    if (charCount + w.word.length > subtitleStyle.max_chars_per_line) {
      lines.push([]);
      charCount = 0;
    }
    lines[lines.length - 1].push(w.word);
    charCount += w.word.length + 1;
  }

  const displayLine = lines[0]?.join(' ') ?? '';

  return (
    <div
      style={{
        position: 'absolute',
        bottom: `${subtitleStyle.bottom_offset_percent}%`,
        left: '50%',
        transform: 'translateX(-50%)',
        background: subtitleStyle.background,
        padding: subtitleStyle.padding,
        borderRadius: subtitleStyle.border_radius,
        fontFamily: playbook.typography.font_family,
        fontSize: subtitleStyle.font_size,
        fontWeight: subtitleStyle.font_weight,
        color: subtitleStyle.color,
        textAlign: 'center',
        maxWidth: '80%',
        zIndex: 20,
        whiteSpace: 'pre-wrap',
        lineHeight: 1.4,
      }}
    >
      {displayLine}
    </div>
  );
};
