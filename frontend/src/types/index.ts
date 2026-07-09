export interface User {
  id: string
  email: string
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface URLItem {
  id: number
  original_url: string
  short_code: string
  short_url: string
  expires_at: string | null
  created_at: string
  user_id: string | null
}

export interface URLCreatePayload {
  original_url: string
  custom_alias?: string
  expires_at?: string
}

export interface DailyClick {
  date: string
  click_count: number
}

export interface CountryClick {
  country_code: string
  click_count: number
}

export interface ReferrerClick {
  referrer: string
  click_count: number
}

export interface AttributeClick {
  name: string
  click_count: number
}

export interface URLAnalytics {
  short_code: string
  original_url: string
  total_clicks: number
  clicks_over_time: DailyClick[]
  top_countries: CountryClick[]
  top_referrers: ReferrerClick[]
  device_breakdown: AttributeClick[]
  browser_breakdown: AttributeClick[]
  os_breakdown: AttributeClick[]
}
