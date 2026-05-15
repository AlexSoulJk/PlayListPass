import { useEffect, useState, type FormEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { consumeServiceConnectionPending } from '../../../../auth/serviceConnectionAccess'
import styles from './ServiceConnectionPage.module.css'

type AccessState = 'checking' | 'allowed' | 'blocked'

export function ServiceConnectionPage() {
  const [accessState, setAccessState] = useState<AccessState>('checking')
  const [token, setToken] = useState('')
  const [submitted, setSubmitted] = useState(false)

  useEffect(() => {
    const isAllowed = consumeServiceConnectionPending()
    setAccessState(isAllowed ? 'allowed' : 'blocked')
  }, [])

  if (accessState === 'checking') {
    return <div className="app-loading">Проверка доступа...</div>
  }

  if (accessState === 'blocked') {
    return <Navigate to="/app/groups" replace />
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSubmitted(true)
  }

  return (
    <section className={styles.root}>
      <h2 className={styles.title}>Подключение сервиса</h2>
      <p className={styles.description}>
        Это мок-экран первого входа после регистрации. Укажите токен музыкального сервиса.
      </p>

      <form className={styles.form} onSubmit={handleSubmit}>
        <label className={styles.label} htmlFor="service-token">
          Токен
        </label>
        <input
          className={styles.input}
          id="service-token"
          onChange={(event) => setToken(event.target.value)}
          placeholder="Введите токен сервиса"
          type="text"
          value={token}
        />

        <button className={styles.submitButton} type="submit">
          Сохранить
        </button>
      </form>

      {submitted ? <p className={styles.note}>Мок: токен принят (без реального сохранения).</p> : null}
    </section>
  )
}
