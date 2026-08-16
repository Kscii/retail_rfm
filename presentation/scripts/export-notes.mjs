import fs from 'node:fs'
import path from 'node:path'

const source = path.resolve(process.argv[2] ?? 'slides.md')
const output = path.resolve(process.argv[3] ?? 'dist/speaker-notes.en.md')
const documentTitle = process.argv[4] ?? 'Online Retail Final Presentation — Speaker Notes'
const markdown = fs.readFileSync(source, 'utf8')
const slides = markdown.split(/\n---\n/g).slice(1)
const notes = slides.map((slide, index) => {
  const matches = [...slide.matchAll(/<!--[\s\S]*?-->/g)]
  const raw = matches.at(-1)?.[0] ?? ''
  const body = raw.replace(/^<!--\s*/, '').replace(/\s*-->$/, '').trim()
  const rawTitle = slide.match(/^#\s+(.+)$/m)?.[1]
  const title = rawTitle?.replace(/^\d+\.\s*/, '') ?? (index === 0 ? 'Title and research question' : `Slide ${index + 1}`)
  return `## ${index + 1}. ${title}\n\n${body}`
})

if (notes.length !== 10)
  throw new Error(`Expected exactly 10 slides, found ${notes.length}`)

fs.mkdirSync(path.dirname(output), { recursive: true })
fs.writeFileSync(output, `# ${documentTitle}\n\n${notes.join('\n\n')}\n`, 'utf8')
console.log(`Wrote ${notes.length} speaker-note sections to ${output}`)
