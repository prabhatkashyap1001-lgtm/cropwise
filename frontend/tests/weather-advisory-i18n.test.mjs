import test from 'node:test'
import assert from 'node:assert/strict'
import {
  localizeInsight,
  localizeAdvisorySummary,
  localizeEtc,
  localizeEtcAssumptions,
  localizeLimitations,
} from '../src/utils/weatherAdvisoryI18n.js'

const locales = ['en', 'hi', 'mr', 'bn', 'ta', 'te', 'gu', 'kn', 'ml', 'pa', 'or', 'as', 'ur', 'bho', 'mai']

test('weather advisory localization exists for all 15 shipped languages', () => {
  for (const code of locales) {
    const result = localizeInsight({
      id: 'heat',
      level: 'high',
      title: 'Heat stress',
      message: 'English server text',
      trigger: 'Highest forecast temperature: 38°C on Mon 26 Oct.',
      basis: 'English server basis',
    }, code)
    assert.ok(result.title, `missing title for ${code}`)
    assert.ok(result.message.includes('38'), `weather measurement lost for ${code}`)
    assert.ok(result.trigger, `missing trigger for ${code}`)
    assert.ok(result.basis, `missing basis for ${code}`)
    assert.notEqual(result.message, 'English server text', `server English leaked for ${code}`)
  }
})

test('advisory summary reflects localized forecast risk', () => {
  for (const code of locales) {
    const summary = localizeAdvisorySummary(code, {
      insights: [{
        id: 'heat', level: 'high', title: 'Heat stress',
        message: 'English server text', trigger: 'Highest forecast temperature: 38°C.',
      }],
    })
    assert.ok(summary.includes('38'), `summary omitted forecast value for ${code}`)
    assert.notEqual(summary, 'No weather risks stand out in the next 7 days.', code)
  }
})

test('ETc and limitations are localized and retain calculation values', () => {
  const etc = { crop: 'Wheat', stage: 'mid', kc: 1.15, days: 7, etc_mm: 23.4 }
  for (const code of locales) {
    const text = localizeEtc(etc, 'Wheat', 'Mid-season', code)
    assert.ok(text.includes('23.4'), `ETc value missing for ${code}`)
    assert.ok(text.includes('7'), `ETc duration missing for ${code}`)
    assert.ok(localizeEtcAssumptions(code).length >= 3, `ETc assumptions missing for ${code}`)
    const limitations = localizeLimitations(['This advice uses demonstration data.'], code)
    assert.ok(limitations.length >= 3, `limitations missing for ${code}`)
  }
})
