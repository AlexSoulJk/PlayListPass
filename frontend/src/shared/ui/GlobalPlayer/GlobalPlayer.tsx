import { usePlayback } from '../../../app/providers/usePlayback'
import styles from './GlobalPlayer.module.css'

export function GlobalPlayer() {
  const {
    currentTrack,
    isPlaying,
    volume,
    canPlayPrevious,
    canPlayNext,
    hidePlayer,
    pauseTrack,
    resumeTrack,
    playPreviousTrack,
    playNextTrack,
    setVolume,
  } = usePlayback()

  if (!currentTrack) {
    return null
  }

  return (
    <section aria-label="Глобальный плеер" className={styles.root}>
      <div className={styles.closeArea}>
        <button aria-label="Скрыть плеер" className={styles.hideButton} onClick={hidePlayer} type="button">
          ×
        </button>
      </div>

      <div className={styles.track}>
        <div
          aria-hidden
          className={styles.cover}
          style={currentTrack.coverUrl ? { backgroundImage: `url(${currentTrack.coverUrl})` } : undefined}
        />
        <div className={styles.meta}>
          <p className={styles.title}>{currentTrack.title}</p>
          <p className={styles.artist}>{currentTrack.artist}</p>
        </div>
      </div>

      <div className={styles.controls}>
        <button
          aria-label="Предыдущий трек"
          className={styles.controlButton}
          disabled={!canPlayPrevious}
          onClick={playPreviousTrack}
          type="button"
        >
          ⏮
        </button>
        {isPlaying ? (
          <button aria-label="Пауза" className={styles.controlButton} onClick={pauseTrack} type="button">
            ⏸
          </button>
        ) : (
          <button aria-label="Воспроизвести" className={styles.controlButton} onClick={resumeTrack} type="button">
            ▶
          </button>
        )}
        <button
          aria-label="Следующий трек"
          className={styles.controlButton}
          disabled={!canPlayNext}
          onClick={playNextTrack}
          type="button"
        >
          ⏭
        </button>
      </div>

      <div className={styles.volumeWrap}>
        <span aria-hidden className={styles.volumeIcon}>
          🔊
        </span>
        <input
          aria-label="Громкость"
          className={styles.volumeRange}
          max={1}
          min={0}
          onChange={(event) => setVolume(Number(event.target.value))}
          step={0.01}
          type="range"
          value={volume}
        />
      </div>
    </section>
  )
}
