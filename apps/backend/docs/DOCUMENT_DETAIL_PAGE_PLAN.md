# Document Detail Page Plan

## Overview
This document outlines the comprehensive plan for the document detail page in DocuLearn, including all features, layouts, and technical considerations.

## Page Structure

### 1. Header Section
- **Document Title/Filename** (prominent display)
- **Breadcrumb Navigation**: Home > Library > [Folder Name] > Document
- **Status Badge**: Processing, Ready, Failed, Archived
- **Action Buttons**:
  - Download Original
  - Export (PDF, Markdown, Text)
  - Move to Folder
  - Archive/Unarchive
  - Delete
  - Share (future feature)

### 2. Document Metadata Panel (collapsible sidebar or card)
- **File Information**:
  - File size (human-readable format)
  - File type/extension icon
  - Upload date/time
  - Last modified
  - File hash (for verification)
  - Word count
  - Page count (if available)
  
- **Organization**:
  - Current folder location (with link)
  - Tags (clickable chips)
  - Add/remove tags functionality

### 3. Main Content Area (tabbed interface)

#### Tab 1: Summary
- AI-generated summary (if available)
- Summary metadata:
  - Generation date
  - LLM model used
  - Processing time
- Actions:
  - Regenerate summary
  - Customize summary (style, length, focus areas)
  - Copy summary
  - Export summary

#### Tab 2: Full Text
- Extracted text display with:
  - Search within document
  - Text highlighting
  - Copy text sections
  - Font size adjustment
  - Reading mode toggle
- Text statistics:
  - Character count
  - Paragraph count
  - Reading time estimate

#### Tab 3: Preview (if PDF)
- Embedded PDF viewer
- Page navigation
- Zoom controls
- Full-screen mode
- Print functionality

#### Tab 4: Analysis (future enhancement)
- Key topics/entities extracted
- Sentiment analysis
- Language detection
- Readability score
- Related documents (based on content similarity)

#### Tab 5: Quizzes
- **Quiz Generation Section**:
  - Generate Quiz button with options:
    - Number of questions (1-50)
    - Question types (Multiple Choice, True/False, Short Answer)
    - Difficulty level (Easy, Medium, Hard, Mixed)
    - Focus areas (optional text input)
  - Generation status indicator (queued, processing, ready)
  
- **Generated Quizzes List**:
  - Cards showing previously generated quizzes
  - Each card displays:
    - Quiz title/ID
    - Number of questions
    - Difficulty level
    - Creation date
    - Last attempt score (if taken)
    - Actions: Take Quiz, View Results, Delete

- **Quiz Taking Interface** (modal or full screen):
  - Question counter (e.g., "Question 3 of 10")
  - Progress bar
  - Question display with:
    - Clear question text
    - Multiple choice options (radio buttons)
    - True/False toggles
    - Text input for short answers
  - Navigation: Previous, Next, Skip
  - Timer (optional)
  - Submit Quiz button

- **Quiz Results View**:
  - Overall score and percentage
  - Question-by-question breakdown:
    - Your answer vs correct answer
    - Explanation for each question
    - Difficulty indicator
  - Performance analytics:
    - Time taken
    - Questions by difficulty
    - Topic performance
  - Actions: Retake Quiz, Generate New Quiz

#### Tab 6: Flashcards
- **Flashcard Generation Section**:
  - Generate Flashcards button with options:
    - Number of cards (1-100)
    - Card types (Definition, Concept, Formula, Fact)
    - Difficulty level (Easy, Medium, Hard, Mixed)
  - Generation status indicator

- **Flashcard Sets**:
  - Grid or list of flashcard sets
  - Each set shows:
    - Set title/ID
    - Number of cards
    - Difficulty distribution
    - Last studied date
    - Progress indicator (cards mastered)
    - Actions: Study, View All, Export, Delete

- **Study Mode** (full screen experience):
  - Card flip animation
  - Front/back card display
  - Optional hints
  - Controls:
    - Flip card (spacebar or click)
    - Next/Previous navigation
    - Shuffle deck
    - Mark as easy/medium/hard
  - Progress tracker: "Card 5 of 20"
  - Session timer

- **Review Interface**:
  - Spaced repetition indicators
  - Confidence ratings (1-5 stars)
  - Time spent per card
  - Cards organized by:
    - Need review
    - Recently learned
    - Mastered
  
- **Flashcard Analytics**:
  - Study streak calendar
  - Cards by confidence level
  - Average review time
  - Learning curve graph
  - Recommended review schedule

### 4. Interactive Features

#### Quick Actions Bar (floating or sticky)
- Quick search within document
- Navigate to sections
- Bookmark/favorite toggle
- Quick share
- Print

#### Annotation System (future enhancement)
- Highlight text passages
- Add notes/comments
- Create bookmarks
- Export annotations

### 5. Related Content Section
- Similar documents (based on tags/content)
- Documents in same folder
- Recently viewed documents
- Recommended reading

### 6. Activity Timeline
- Document history:
  - Upload event
  - Processing status changes
  - Tag additions/removals
  - Folder moves
  - Summary generations
  - Export/download events

### 7. Study Dashboard (overview across tabs)
- Combined progress metrics
- Study suggestions based on:
  - Time since last review
  - Performance trends
  - Spaced repetition algorithm
- Achievement badges
- Study streak tracking

## Mobile Responsive Design

### General Mobile Features
- Collapsible panels for mobile
- Swipeable tabs
- Touch-friendly controls
- Optimized PDF viewer for mobile
- Bottom sheet for actions

### Quiz Mobile UI
- Swipe gestures for navigation
- Large touch targets for options
- Collapsible question panel
- Bottom sheet for quiz settings

### Flashcard Mobile UI
- Swipe to flip cards
- Swipe left/right for navigation
- Gesture-based difficulty rating
- Full-screen study mode
- Haptic feedback on interactions

## Export/Import Options

### Quiz Export Formats
- PDF worksheets
- Anki decks
- CSV format

### Flashcard Export Formats
- Anki decks
- Quizlet sets
- PDF study sheets
- Physical card print layouts

## Gamification Elements
- Points for completing quizzes
- Streaks for daily study
- Leaderboards (optional)
- Achievement unlocks
- Progress milestones

## Error Handling
- Clear error messages if processing failed
- Retry processing button
- Support/help information
- Fallback content display

## Performance Considerations
- Lazy load tabs content
- Virtual scrolling for long texts
- Progressive PDF loading
- Cache frequently accessed data
- Optimize for large documents
- Lazy load quiz/flashcard data
- Cache frequently used sets
- Offline mode for studying
- Background sync for progress
- Optimistic UI updates

## Accessibility Features
- Keyboard navigation
- Screen reader support
- High contrast mode
- Adjustable text size
- Focus indicators
- ARIA labels

## Technical Implementation Notes

### Architecture
1. Use Angular signals for reactive state
2. Implement route resolver for initial data
3. Use virtual scrolling for long content
4. Implement service worker for offline PDF viewing
5. Add loading skeletons for better UX
6. Use intersection observer for lazy loading
7. Implement proper error boundaries
8. Add analytics tracking for user actions

### Data Models Required
- `DocumentDetail` - Full document information
- `DocumentSummary` - AI-generated summaries
- `Quiz` - Quiz questions and metadata
- `QuizResult` - User's quiz attempts and scores
- `FlashcardSet` - Collection of flashcards
- `FlashcardProgress` - User's learning progress
- `StudySession` - Track study activities

### API Endpoints Needed
- `GET /api/v1/document/{id}` - Get document details
- `GET /api/v1/document/{id}/summary` - Get or generate summary
- `POST /api/v1/quiz/document/{id}/generate` - Generate quiz
- `GET /api/v1/quiz/{id}` - Get quiz details
- `POST /api/v1/quiz/{id}/submit` - Submit quiz answers
- `POST /api/v1/flashcard/document/{id}/generate` - Generate flashcards
- `GET /api/v1/flashcard/set/{id}` - Get flashcard set
- `POST /api/v1/flashcard/session` - Track study session

### State Management
- Document details state
- Quiz generation and results state
- Flashcard sets and progress state
- UI state (active tab, loading states, etc.)
- Study progress state

## Future Enhancements

### Collaborative Features
- Share quiz/flashcard sets
- Public/private visibility
- Clone and modify sets
- Community ratings

### AI Enhancement Options
- Regenerate specific questions/cards
- Adjust difficulty dynamically
- Generate variations
- Focus on weak areas
- Custom prompts for generation

### Advanced Analytics
- Learning patterns analysis
- Recommendation engine
- Performance predictions
- Study time optimization

## Success Metrics
- User engagement with learning tools
- Quiz completion rates
- Flashcard review consistency
- Time spent studying
- Learning outcome improvements
- Feature adoption rates

## Implementation Phases

### Phase 1: Core Document Display
- Basic document details
- Summary tab
- Full text view
- PDF preview

### Phase 2: Learning Tools
- Quiz generation and taking
- Flashcard generation and study
- Basic progress tracking

### Phase 3: Enhanced Features
- Advanced analytics
- Export/import functionality
- Mobile optimizations
- Gamification elements

### Phase 4: Social & AI Features
- Collaborative features
- AI enhancements
- Advanced recommendations
- Community features