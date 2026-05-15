import { useTheme } from '../../../app/theme/useTheme'
import type { AppTheme } from '../../../app/theme/themeTypes'
import styles from './ThemeToggle.module.css'

type ToggleItem = {
  id: AppTheme
  label: string
  circleClassName: string
}

const items: ToggleItem[] = [
  { id: 'dark', label: 'Черная тема', circleClassName: 'darkCircle' },
  { id: 'red', label: 'Красная тема', circleClassName: 'redCircle' },
]

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  return (
    <section aria-label="Переключение темы" className={styles.root}>
      <p className={styles.title}>Тема</p>
      <div className={styles.group} role="radiogroup" aria-label="Цветовая тема приложения">
        {items.map((item) => {
          const isActive = theme === item.id
          const classNames = [styles.button, isActive ? styles.buttonActive : ''].filter(Boolean).join(' ')
          return (
            <button
              aria-checked={isActive}
              aria-label={item.label}
              className={classNames}
              key={item.id}
              onClick={() => setTheme(item.id)}
              role="radio"
              type="button"
            >
              <span className={item.circleClassName === 'darkCircle' ? styles.darkCircle : styles.redCircle} />
            </button>
          )
        })}
      </div>
    </section>
  )
}

