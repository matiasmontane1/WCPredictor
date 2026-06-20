const FLAGS: Record<string, string> = {
  // Americas
  'Argentina': '🇦🇷', 'Bolivia': '🇧🇴', 'Brazil': '🇧🇷', 'Canada': '🇨🇦',
  'Chile': '🇨🇱', 'Colombia': '🇨🇴', 'Costa Rica': '🇨🇷', 'Ecuador': '🇪🇨',
  'El Salvador': '🇸🇻', 'Guatemala': '🇬🇹', 'Haiti': '🇭🇹', 'Honduras': '🇭🇳',
  'Jamaica': '🇯🇲', 'Mexico': '🇲🇽', 'Panama': '🇵🇦', 'Paraguay': '🇵🇾',
  'Peru': '🇵🇪', 'Trinidad and Tobago': '🇹🇹', 'United States': '🇺🇸',
  'Uruguay': '🇺🇾', 'Venezuela': '🇻🇪', 'Cuba': '🇨🇺',
  // Europe
  'Albania': '🇦🇱', 'Austria': '🇦🇹', 'Belgium': '🇧🇪', 'Bosnia and Herzegovina': '🇧🇦',
  'Croatia': '🇭🇷', 'Czech Republic': '🇨🇿', 'Czechia': '🇨🇿', 'Denmark': '🇩🇰',
  'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'France': '🇫🇷', 'Georgia': '🇬🇪', 'Germany': '🇩🇪',
  'Greece': '🇬🇷', 'Hungary': '🇭🇺', 'Italy': '🇮🇹', 'Kosovo': '🇽🇰',
  'Netherlands': '🇳🇱', 'North Macedonia': '🇲🇰', 'Norway': '🇳🇴', 'Poland': '🇵🇱',
  'Portugal': '🇵🇹', 'Romania': '🇷🇴', 'Scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 'Serbia': '🇷🇸',
  'Slovakia': '🇸🇰', 'Slovenia': '🇸🇮', 'Spain': '🇪🇸', 'Sweden': '🇸🇪',
  'Switzerland': '🇨🇭', 'Turkey': '🇹🇷', 'Ukraine': '🇺🇦', 'Wales': '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
  // Africa
  'Algeria': '🇩🇿', 'Cameroon': '🇨🇲', 'Côte d\'Ivoire': '🇨🇮', "Ivory Coast": '🇨🇮',
  'DR Congo': '🇨🇩', 'Egypt': '🇪🇬', 'Ghana': '🇬🇭', 'Kenya': '🇰🇪',
  'Mali': '🇲🇱', 'Morocco': '🇲🇦', 'Nigeria': '🇳🇬', 'Senegal': '🇸🇳',
  'South Africa': '🇿🇦', 'Tunisia': '🇹🇳', 'Zambia': '🇿🇲', 'Zimbabwe': '🇿🇼',
  // Asia
  'Australia': '🇦🇺', 'China PR': '🇨🇳', 'China': '🇨🇳', 'India': '🇮🇳',
  'Indonesia': '🇮🇩', 'Iran': '🇮🇷', 'Iraq': '🇮🇶', 'Japan': '🇯🇵',
  'Jordan': '🇯🇴', 'Korea Republic': '🇰🇷', 'South Korea': '🇰🇷', 'Kuwait': '🇰🇼',
  'New Zealand': '🇳🇿', 'Oman': '🇴🇲', 'Qatar': '🇶🇦', 'Saudi Arabia': '🇸🇦',
  'Thailand': '🇹🇭', 'United Arab Emirates': '🇦🇪', 'Uzbekistan': '🇺🇿',
  // Others
  'Israel': '🇮🇱', 'Russia': '🇷🇺',
}

export function getFlag(teamName: string): string {
  return FLAGS[teamName] ?? '🏳️'
}
