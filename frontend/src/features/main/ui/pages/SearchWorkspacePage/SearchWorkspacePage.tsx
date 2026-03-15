import { SectionMockCard } from '../../components/SectionMockCard/SectionMockCard'
import styles from './SearchWorkspacePage.module.css'

const mockResults = ['Найденный трек 01', 'Найденный трек 02', 'Найденный трек 03', 'Найденный трек 04']

export function SearchWorkspacePage() {
  return (
    <SectionMockCard
      description="Мок-раздел поиска. Здесь появится поиск по трекам, артистам и плейлистам с фильтрами."
      title="Поиск"
    >
      <div className={styles.searchBar}>Поле поиска (mock)</div>
      <ul className={styles.results}>
        {mockResults.map((item) => (
          <li className={styles.resultItem} key={item}>
            {item}
          </li>
        ))}
      </ul>
    </SectionMockCard>
  )
}
