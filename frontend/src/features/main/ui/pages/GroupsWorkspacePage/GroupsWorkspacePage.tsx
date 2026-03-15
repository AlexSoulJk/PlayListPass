import { useState } from 'react'
import styles from './GroupsWorkspacePage.module.css'

type GroupMemberRole = 'host' | 'guest' | 'viewer'

type GroupMember = {
  id: string
  name: string
  role: GroupMemberRole
}

type GroupCard = {
  id: string
  name: string
}

const groupsMock: GroupCard[] = [
  { id: 'group-1', name: 'Roadtrip Vibes' },
  { id: 'group-2', name: 'Night Coding' },
  { id: 'group-3', name: 'Morning Boost' },
  { id: 'group-4', name: 'Workout Team' },
  { id: 'group-5', name: 'Study Flow' },
  { id: 'group-6', name: 'Party House' },
  { id: 'group-7', name: 'Jazz Evening' },
]

const membersMock: GroupMember[] = [
  { id: 'member-1', name: 'Вы', role: 'host' },
  { id: 'member-2', name: 'Имя участника', role: 'guest' },
  { id: 'member-3', name: 'Имя участника', role: 'guest' },
  { id: 'member-4', name: 'Имя участника', role: 'viewer' },
]

const roleLabel: Record<GroupMemberRole, string> = {
  host: 'host',
  guest: 'guest',
  viewer: 'viewer',
}

export function GroupsWorkspacePage() {
  const [activeGroupId, setActiveGroupId] = useState(groupsMock[2].id)
  const activeGroup = groupsMock.find((group) => group.id === activeGroupId) ?? groupsMock[0]

  return (
    <section className={styles.root}>
      <section className={styles.groupListSection}>
        <header className={styles.groupListHeader}>
          <h2 className={styles.groupListTitle}>Группы</h2>
          <button className={styles.editButton} type="button">
            <svg aria-hidden viewBox="0 0 24 24">
              <path d="M4 20L8.5 19L19 8.5L14.5 4L4 14.5L4 20Z" />
              <path d="M12.8 5.7L17.3 10.2" />
            </svg>
          </button>
        </header>

        <div className={styles.groupList}>
          {groupsMock.map((group) => (
            <button
              className={group.id === activeGroup.id ? `${styles.groupCard} ${styles.groupCardActive}` : styles.groupCard}
              key={group.id}
              onClick={() => setActiveGroupId(group.id)}
              type="button"
            >
              <span className={styles.avatar} aria-hidden />
              <span className={styles.groupName}>{group.name}</span>
            </button>
          ))}
        </div>
      </section>

      <section className={styles.detailsSection}>
        <button className={styles.backButton} type="button">
          <svg aria-hidden viewBox="0 0 24 24">
            <path d="M14.5 5.5L8 12L14.5 18.5" />
          </svg>
        </button>

        <div className={styles.detailsHeader}>
          <div className={styles.detailsAvatar} aria-hidden />
          <h3 className={styles.detailsName}>{activeGroup.name}</h3>
        </div>

        <div className={styles.linkBlocks}>
          <button className={styles.linkBlock} type="button">
            <span>Плейлисты группы</span>
            <span className={styles.linkArrow}>›</span>
          </button>
          <button className={styles.linkBlock} type="button">
            <span>QR-код группы</span>
            <span className={styles.linkArrow}>›</span>
          </button>
        </div>

        <div className={styles.membersCard}>
          {membersMock.map((member) => (
            <div className={styles.memberRow} key={member.id}>
              <span className={styles.memberAvatar} aria-hidden />
              <span className={styles.memberName}>{member.name}</span>
              <span className={styles.memberRole}>{roleLabel[member.role]}</span>
            </div>
          ))}
        </div>

        <button className={styles.deleteButton} type="button">
          Удалить группу
        </button>
      </section>
    </section>
  )
}
