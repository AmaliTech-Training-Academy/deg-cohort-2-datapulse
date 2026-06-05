// ── Raw API type (from UserListSerializer) ────────────────────────────────────

export interface ApiAdminUser {
  readonly id: string;
  readonly email: string;
  readonly first_name: string;
  readonly last_name: string;
  readonly role: 'admin' | 'user';
  readonly is_active: boolean;
  readonly last_login: string | null;
  readonly created_at: string;
  readonly is_email_verified: boolean;
  readonly datasets_count: number;
}

export interface ApiAdminUsersResponse {
  readonly count: number;
  readonly next: string | null;
  readonly previous: string | null;
  readonly results: ApiAdminUser[];
}

// ── Frontend view model ───────────────────────────────────────────────────────

export interface AdminUser {
  readonly id: string;
  readonly email: string;
  readonly fullName: string;
  readonly firstName: string;
  readonly lastName: string;
  readonly role: 'admin' | 'user';
  readonly isActive: boolean;
  readonly lastLogin: string | null;
  readonly createdAt: string;
  readonly isEmailVerified: boolean;
  readonly datasetsCount: number;
}

// ── Mapping ───────────────────────────────────────────────────────────────────

export function mapAdminUser(raw: ApiAdminUser): AdminUser {
  return {
    id: raw.id,
    email: raw.email,
    firstName: raw.first_name,
    lastName: raw.last_name,
    fullName: `${raw.first_name} ${raw.last_name}`.trim() || raw.email,
    role: raw.role,
    isActive: raw.is_active,
    lastLogin: raw.last_login,
    createdAt: raw.created_at,
    isEmailVerified: raw.is_email_verified,
    datasetsCount: raw.datasets_count,
  };
}
