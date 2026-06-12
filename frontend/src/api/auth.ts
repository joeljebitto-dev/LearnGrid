import { apiClient, storeTokens, type TokenPair } from './client';

export type RoleAssignment = {
  id: string;
  role_code: string;
  role_name: string;
  scope_type: 'platform' | 'institution' | 'course' | 'assessment';
  scope_id: string | null;
  assigned_at: string;
};

export type Session = {
  account_id: string;
  email: string;
  status: string;
  primary_role: string | null;
  role_assignments: RoleAssignment[];
};

export type UserProfile = {
  id: string;
  auth_account_id: string;
  institution_id: string | null;
  first_name: string;
  last_name: string;
  display_name: string | null;
  avatar_url: string | null;
  status: string;
  metadata: Record<string, unknown>;
  profile_type: 'student' | 'instructor' | 'admin' | null;
  role_profile: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type OidcConfig = {
  enabled: boolean;
  provider: string;
  provider_label: string;
  scopes: string[];
};

export type OidcAuthorizeResponse = {
  authorization_url: string;
  state: string;
  expires_at: string;
};

export type OidcCallbackPayload = {
  code: string;
  state: string;
};

export type SessionContext = {
  session: Session;
  profile: UserProfile;
};

export async function login(payload: LoginPayload): Promise<TokenPair> {
  const response = await apiClient.post<TokenPair>('/auth/token/issue/', payload);
  storeTokens(response.data);
  return response.data;
}

export async function getOidcConfig(): Promise<OidcConfig> {
  const response = await apiClient.get<OidcConfig>('/auth/oidc/config/');
  return response.data;
}

export async function startOidcAuthorization(): Promise<OidcAuthorizeResponse> {
  const response = await apiClient.post<OidcAuthorizeResponse>('/auth/oidc/authorize/', {});
  return response.data;
}

export async function completeOidcCallback(payload: OidcCallbackPayload): Promise<TokenPair> {
  const response = await apiClient.post<TokenPair>('/auth/oidc/callback/', payload);
  storeTokens(response.data);
  return response.data;
}

export async function getSession(): Promise<Session> {
  const response = await apiClient.get<Session>('/auth/session/');
  return response.data;
}

export async function getCurrentProfile(): Promise<UserProfile> {
  const response = await apiClient.get<UserProfile>('/users/profiles/me/');
  return response.data;
}

export async function getSessionContext(): Promise<SessionContext> {
  const [session, profile] = await Promise.all([getSession(), getCurrentProfile()]);
  return { session, profile };
}

export function portalForRole(role: string | null): 'admin' | 'instructor' | 'student' | 'none' {
  if (role === 'super_admin' || role === 'institution_admin') {
    return 'admin';
  }
  if (role === 'instructor' || role === 'teaching_assistant') {
    return 'instructor';
  }
  if (role === 'student') {
    return 'student';
  }
  return 'none';
}
