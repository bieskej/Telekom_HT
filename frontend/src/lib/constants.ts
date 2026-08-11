/** Radix Select ne dopušta prazan string kao value. */
export const FILTER_ALL = '__all__'

export function filterValueToApi(value: string): string | undefined {
  return value === FILTER_ALL || value === '' ? undefined : value
}
