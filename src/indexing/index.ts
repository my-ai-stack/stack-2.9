// Stack 2.9 Indexing Module
//
// Semantic code search (RAG) for codebase understanding.

export {
  CodeIndexer,
  createIndexer,
} from './CodeIndexer.ts'

export type {
  CodeChunk,
  CodeIndex,
  CodeSearchResult,
} from './CodeIndexer.ts'

export default {
  createIndexer,
}