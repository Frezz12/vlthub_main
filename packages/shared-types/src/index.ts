// ─── Auth ───────────────────────────────────────────────
export interface RegisterRequest {
  email: string
  password: string
  nickname: string
  username: string
  referral_code?: string | null
}

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  user: UserOut
  has_pin: boolean
}

export interface RefreshRequest {
  refresh_token: string
}

export interface TelegramAuthRequest {
  id: number
  first_name: string
  username?: string
  photo_url?: string
  auth_date: number
  hash: string
}

// ─── Badge ──────────────────────────────────────────────
export interface BadgeOut {
  id: string
  name: string
  icon_svg: string
  description: string | null
  avatar_ring_gradient: string | null
  avatar_ring_effect: string | null
  created_at: string
}

export interface UserBadgeBrief {
  id: string
  name: string
  icon_svg: string
  description?: string | null
  avatar_ring_gradient?: string | null
  avatar_ring_effect?: string | null
  is_active: boolean
}

export interface UserBadgeOut {
  badge: BadgeOut
  is_active: boolean
}

// ─── User ───────────────────────────────────────────────
export interface UserOut {
  id: string
  email: string
  nickname: string
  username: string
  bio: string | null
  avatar_url: string | null
  cover_url?: string | null
  is_public: boolean
  is_email_confirmed: boolean
  social_links: SocialLinkOut[]
  settings: Record<string, any>
  created_at: string
  is_admin?: boolean
  referral_code: string
  referrals_count?: number
  storage_limit?: number
  storage_used?: number
  badges?: UserBadgeBrief[]
  active_badge?: UserBadgeBrief | null
}

export interface UserProfileOut {
  id: string
  nickname: string
  username: string
  bio: string | null
  avatar_url: string | null
  cover_url?: string | null
  is_public: boolean
  created_at: string
  social_links: SocialLinkOut[]
  project_count: number
  version_count: number
  collaboration_count: number
  follower_count: number
  following_count: number
  is_following: boolean
  projects: ProjectOut[]
  active_badge?: UserBadgeBrief | null
}

export interface UserUpdate {
  nickname?: string
  bio?: string
  is_public?: boolean
}

export interface SocialLinkOut {
  platform: string
  url: string
}

export interface SocialLinkUpdate {
  links: { platform: string; url: string }[]
}

export interface UserSearchResult {
  id: string
  nickname: string
  username: string
  avatar_url: string | null
  is_following: boolean
  active_badge?: UserBadgeBrief | null
}

export interface FollowOut {
  id: string
  nickname: string
  username: string
  avatar_url: string | null
  active_badge?: UserBadgeBrief | null
  followed_at: string
}

// ─── Project ────────────────────────────────────────────
export type DawType = 'logic_pro' | 'ableton' | 'fl_studio' | 'cubase' | 'reaper' | 'studio_one' | 'bitwig' | 'other'
export type CollaboratorRole = 'owner' | 'editor' | 'commentator' | 'viewer'
export type CollaboratorStatus = 'pending' | 'accepted' | 'declined'
export type AccessRole = 'editor' | 'commentator' | 'viewer'

export interface ProjectCreate {
  title: string
  artists?: string | null
  sample_rate?: number | null
  daw_type: DawType
  bpm?: number | null
  key?: string | null
  beatmaker?: string | null
  status?: string
  description?: string | null
  project_path?: string | null
  tags?: string[]
  is_public?: boolean
}

export interface ProjectUpdate {
  title?: string
  artists?: string | null
  sample_rate?: number | null
  bpm?: number | null
  key?: string | null
  beatmaker?: string | null
  status?: string
  description?: string | null
  lyrics?: string | null
  cover_url?: string | null
  daw_type?: string | null
  project_path?: string | null
  is_public?: boolean | null
  is_archived?: boolean | null
  is_favorite?: boolean | null
  tags?: string[]
}

export interface ProjectUpdate {
  title?: string
  artists?: string | null
  sample_rate?: number | null
  bpm?: number | null
  key?: string | null
  beatmaker?: string | null
  status?: string
  description?: string | null
  lyrics?: string | null
  cover_url?: string | null
  project_path?: string | null
  daw_type?: string | null
  is_archived?: boolean | null
  is_favorite?: boolean | null
  tags?: string[]
}

export interface UserBrief {
  id: string
  nickname: string
  username: string
  avatar_url: string | null
}

export interface ProjectOut {
  id: string
  owner_id: string
  owner: UserBrief | null
  title: string
  artists: string | null
  sample_rate: number | null
  bpm: number | null
  key: string | null
  beatmaker: string | null
  status: string
  description: string | null
  lyrics?: string | null
  cover_url: string | null
  daw_type: DawType | null
  project_path?: string | null
  my_project_path?: string | null
  is_public: boolean
  is_archived: boolean
  is_favorite: boolean
  version_count?: number
  total_size?: number
  tags: string[]
  collaborators: CollaboratorOut[]
  created_at: string
  updated_at: string
  access_granted_at?: string | null
}

export interface ProjectListOut {
  items: ProjectOut[]
  total: number
  page: number
  limit: number
}

export interface CollaboratorOut {
  user_id: string
  nickname: string
  username: string
  avatar_url: string | null
  role: CollaboratorRole
  status: CollaboratorStatus
}

export interface CollaboratorInvite {
  email_or_username: string
  role: CollaboratorRole
}

export interface CollaboratorUpdate {
  role: CollaboratorRole
}

export interface AccessUpdate {
  role: AccessRole
}

export interface ShareLinkCreate {
  expires_at?: string | null
  password?: string | null
  role: AccessRole
}

export interface ShareLinkOut {
  id: string
  token: string
  role: AccessRole
  expires_at: string | null
  created_at: string
}

// ─── Version ────────────────────────────────────────────
export interface VersionCreate {
  title: string
  description?: string | null
}

export interface VersionUpdate {
  title?: string
  description?: string | null
}

export interface VersionOut {
  id: string
  project_id: string
  version_number: number
  title: string
  description: string | null
  created_by: string | null
  file_path: string | null
  file_size: number | null
  file_hash: string | null
  is_current: boolean
  audio_previews: AudioPreviewOut[]
  comments_count: number
  created_at: string
  updated_at: string
}

export interface VersionListOut {
  items: VersionOut[]
  total: number
}

export interface VersionFileOut {
  id: string
  version_id?: string | null
  file_name: string
  file_size: number
  file_hash?: string | null
  created_at?: string | null
}

export interface AudioPreviewCreate {
  title: string
  duration?: number | null
}

export interface AudioPreviewOut {
  id: string
  version_id: string
  file_path: string
  title: string
  duration: number | null
  file_size: number
  created_at: string
}

export interface CommentCreate {
  text: string
}

export interface CommentOut {
  id: string
  version_id: string
  user_id: string
  nickname: string
  username: string
  avatar_url: string | null
  text: string
  created_at: string
}

export interface CompareRequest {
  version_1_id: string
  version_2_id: string
}

export interface CompareResult {
  version_1: VersionOut
  version_2: VersionOut
  differences: {
    file_size_changed: boolean
    file_hash_changed: boolean
    size_diff_bytes: number
  }
}

// ─── Notification ──────────────────────────────────────
export type NotificationType =
  | 'collaborator_invite'
  | 'new_version'
  | 'version_approved'
  | 'new_comment'
  | 'project_shared'
  | 'collaborator_accepted'
  | 'new_follower'
  | 'access_request'
  | 'access_granted'
  | 'access_denied'
  | 'setup_pin'

export interface NotificationOut {
  id: string
  type: NotificationType
  message: string
  is_read: boolean
  related_project_id: string | null
  related_version_id: string | null
  related_user_id: string | null
  created_at: string
}

export interface NotificationListOut {
  items: NotificationOut[]
  total: number
  unread_count: number
}

// ─── Version Tasks ──────────────────────────────────────
export interface VersionTaskOut {
  id: string
  version_id: string
  text: string
  is_done: boolean
  position: number
  created_at: string
}

export interface VersionTaskCreate {
  text: string
}

export interface VersionTaskUpdate {
  text?: string
  is_done?: boolean
  position?: number
}

// ─── Search ─────────────────────────────────────────────
export interface SearchParams {
  q: string
  type?: string
  daw?: DawType
  page?: number
  limit?: number
}

export interface SearchResult {
  items: ProjectOut[]
  total: number
  page: number
  limit: number
}

// ─── Activity ──────────────────────────────────────────
export interface ActivityDay {
  date: string
  count: number
}

export interface ActivityResponse {
  items: ActivityDay[]
  total: number
}

// ─── Project activity log (timeline) ─────────────────────
export interface ProjectActivityUserBrief {
  nickname: string
  username: string
  avatar_url: string | null
}

export interface ProjectActivityOut {
  id: string
  event_type: string
  created_at: string
  version_id: string | null
  details: Record<string, unknown> | null
  user: ProjectActivityUserBrief
}

export interface ProjectActivityListOut {
  items: ProjectActivityOut[]
  total: number
}

// ─── Access Requests ────────────────────────────────────
export interface ProjectAccessRequestOut {
  id: string
  project_id: string
  requester_id: string
  requester_nickname: string
  requester_username: string
  requester_avatar: string | null
  status: string
  created_at: string
}

export interface AccessRequestAction {
  action: 'approve' | 'deny'
}

// ─── Pagination ─────────────────────────────────────────
export interface PaginationParams {
  page?: number
  limit?: number
}
