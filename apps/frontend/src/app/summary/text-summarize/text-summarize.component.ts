import {
  Component,
  inject,
  signal,
  computed,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { SummaryService } from '../summary.service';
import { SummaryOptions, SummaryStyle, Summary } from '../summary.model';

@Component({
  selector: 'app-text-summarize',
  standalone: true,
  imports: [CommonModule, FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8 animate-fade-in">
      <div class="text-center mb-8">
        <h1 class="text-3xl sm:text-4xl font-bold text-foreground mb-4">
          Text Summarizer
        </h1>
        <p class="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto">
          Paste or type your text below to get an AI-powered summary. Perfect
          for articles, emails, and any text content.
        </p>
      </div>

      <!-- Input Section -->
      @if (!summarizing() && !success()) {
      <div class="space-y-6">
        <div class="glass rounded-2xl p-6 sm:p-8">
          <div class="mb-4">
            <label
              for="text-input"
              class="block text-sm font-medium text-foreground mb-2"
            >
              Enter your text
            </label>
            <textarea
              id="text-input"
              [(ngModel)]="inputText"
              placeholder="Paste or type your text here..."
              rows="10"
              class="w-full px-4 py-3 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              [class.border-error]="showError()"
            ></textarea>
            <div class="mt-2 flex justify-between items-center">
              <span class="text-sm text-muted-foreground">
                {{ wordCount() }} words
              </span>
              @if (showError()) {
              <span class="text-sm text-error">
                Please enter at least 50 words
              </span>
              }
            </div>
          </div>

          <!-- Summary Options -->
          <div class="mb-6">
            <div class="block text-sm font-medium text-foreground mb-2">
              Summary Style
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
              @for (style of summaryStyles; track style.value) {
              <button
                (click)="selectedStyle.set(style.value)"
                [class.bg-primary-600]="selectedStyle() === style.value"
                [class.text-white]="selectedStyle() === style.value"
                [class.bg-muted]="selectedStyle() !== style.value"
                class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                {{ style.label }}
              </button>
              }
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="flex flex-col sm:flex-row gap-3">
            <button
              (click)="summarizeText()"
              [disabled]="!canSummarize()"
              class="flex-1 px-6 py-3 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-700 hover:to-accent-700 disabled:from-gray-400 disabled:to-gray-500 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] disabled:transform-none transition-all disabled:cursor-not-allowed"
            >
              <span class="flex items-center justify-center">
                <svg
                  class="w-5 h-5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  />
                </svg>
                Generate Summary
              </span>
            </button>
            <button
              (click)="clearText()"
              [disabled]="!inputText()"
              class="px-6 py-3 bg-muted hover:bg-muted/80 disabled:bg-muted/50 text-foreground font-medium rounded-xl transition-colors disabled:cursor-not-allowed"
            >
              Clear
            </button>
          </div>
        </div>

        <!-- Example Templates -->
        <div class="glass rounded-xl p-6">
          <h3 class="text-lg font-semibold text-foreground mb-4">
            Try an example
          </h3>
          <div class="grid gap-3">
            @for (example of examples; track example.title) {
            <button
              (click)="useExample(example)"
              class="text-left p-4 bg-muted/50 hover:bg-muted rounded-lg transition-colors group"
            >
              <h4
                class="font-medium text-foreground group-hover:text-primary-600 dark:group-hover:text-primary-400"
              >
                {{ example.title }}
              </h4>
              <p class="text-sm text-muted-foreground mt-1">
                {{ example.description }}
              </p>
            </button>
            }
          </div>
        </div>
      </div>
      }

      <!-- Processing State -->
      @if (summarizing()) {
      <div class="glass rounded-2xl p-12 text-center">
        <div class="mx-auto w-20 h-20 relative mb-6">
          <div
            class="absolute inset-0 rounded-full border-4 border-muted animate-pulse-soft"
          ></div>
          <div
            class="absolute inset-0 rounded-full border-4 border-primary-600 border-t-transparent animate-spin"
          ></div>
        </div>
        <h2 class="text-2xl font-bold text-foreground mb-2">
          Generating Summary
        </h2>
        <p class="text-muted-foreground">This usually takes 5-10 seconds...</p>
      </div>
      }

      <!-- Success State -->
      @if (success() && summary()) {
      <div class="space-y-6 animate-fade-in">
        <div class="glass rounded-2xl p-6 sm:p-8">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-2xl font-bold text-foreground">
              Summary Generated
            </h2>
            <div class="flex items-center gap-2 text-sm text-muted-foreground">
              <svg
                class="w-4 h-4 text-accent-600 dark:text-accent-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              <span>{{ summary()!.processingTime.toFixed(1) }}s</span>
            </div>
          </div>

          <!-- Summary Content -->
          <div class="prose prose-gray dark:prose-invert max-w-none mb-6">
            <div class="text-foreground/90 leading-relaxed whitespace-pre-wrap">
              {{ summary()!.content }}
            </div>
          </div>

          <!-- Summary Stats -->
          <div
            class="flex flex-wrap gap-4 text-sm text-muted-foreground border-t border-border pt-4"
          >
            <div class="flex items-center gap-1">
              <svg
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <span>{{ summary()!.wordCount }} words</span>
            </div>
            <div class="flex items-center gap-1">
              <svg
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                />
              </svg>
              <span>{{ compressionRatio() }}% reduction</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex flex-col sm:flex-row gap-3 mt-6">
            <button
              (click)="copyToClipboard()"
              class="flex-1 px-6 py-3 bg-muted hover:bg-muted/80 text-foreground font-medium rounded-xl transition-colors flex items-center justify-center"
            >
              @if (copied()) {
              <svg
                class="w-5 h-5 mr-2 text-success-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M5 13l4 4L19 7"
                />
              </svg>
              Copied! } @else {
              <svg
                class="w-5 h-5 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
              Copy Summary }
            </button>
            <button
              (click)="summarizeAnother()"
              class="flex-1 px-6 py-3 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-700 hover:to-accent-700 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all"
            >
              Summarize Another
            </button>
          </div>
        </div>
      </div>
      }

      <!-- Error State -->
      @if (error()) {
      <div class="glass rounded-2xl p-8 text-center border border-error/20">
        <div
          class="mx-auto w-20 h-20 rounded-full bg-error/10 flex items-center justify-center mb-6"
        >
          <svg
            class="w-10 h-10 text-error"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-foreground mb-2">
          Summarization Failed
        </h2>
        <p class="text-muted-foreground mb-6 max-w-md mx-auto">
          {{ error() }}
        </p>
        <button
          (click)="tryAgain()"
          class="px-6 py-3 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-700 hover:to-accent-700 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all"
        >
          Try Again
        </button>
      </div>
      }
    </div>
  `,
  styles: [],
})
export class TextSummarizeComponent {
  private summaryService = inject(SummaryService);
  private router = inject(Router);

  // State
  inputText = signal('');
  summarizing = signal(false);
  success = signal(false);
  error = signal<string | null>(null);
  summary = signal<Summary | null>(null);
  copied = signal(false);
  selectedStyle = signal<SummaryStyle>(SummaryStyle.BALANCED);
  showError = signal(false);

  // Summary style options
  summaryStyles = [
    { value: SummaryStyle.CONCISE, label: 'Concise' },
    { value: SummaryStyle.BALANCED, label: 'Balanced' },
    { value: SummaryStyle.DETAILED, label: 'Detailed' },
    { value: SummaryStyle.BULLET_POINTS, label: 'Bullets' },
  ];

  // Example templates
  examples: Array<{ title: string; description: string; text: string }> = [
    {
      title: 'Scientific Article',
      description: 'Try with a research paper or scientific article',
      text: `Artificial intelligence (AI) has emerged as one of the most transformative technologies of the 21st century, fundamentally reshaping how we approach complex problems across various domains. Machine learning, a subset of AI, enables computers to learn from data without being explicitly programmed, while deep learning uses neural networks with multiple layers to progressively extract higher-level features from raw input.

Recent advances in natural language processing have led to the development of large language models that can understand and generate human-like text with remarkable accuracy. These models, trained on vast amounts of text data, have demonstrated capabilities in tasks ranging from translation and summarization to creative writing and code generation.

The implications of AI extend far beyond technology companies. In healthcare, AI systems are being used to diagnose diseases, predict patient outcomes, and accelerate drug discovery. In finance, machine learning algorithms detect fraudulent transactions and optimize trading strategies. Transportation is being revolutionized by autonomous vehicles that use computer vision and sensor fusion to navigate complex environments.

However, the rapid advancement of AI also raises important ethical considerations. Issues such as bias in algorithms, privacy concerns, job displacement, and the need for explainable AI systems require careful attention from researchers, policymakers, and society at large. As we continue to integrate AI into critical systems, ensuring transparency, fairness, and accountability becomes paramount.`,
    },
    {
      title: 'Business Report',
      description: 'Sample quarterly business performance report',
      text: `Q4 2023 Performance Summary

Executive Overview:
The fourth quarter of 2023 marked a significant milestone for our organization, with total revenue reaching $45.2 million, representing a 23% year-over-year increase. This growth was primarily driven by strong performance in our cloud services division and successful expansion into the Asian market.

Key Financial Highlights:
- Revenue: $45.2M (+23% YoY)
- Operating Income: $12.1M (+18% YoY)
- Net Profit Margin: 26.8% (up from 24.2% in Q4 2022)
- Customer Acquisition: 2,847 new enterprise clients
- Customer Retention Rate: 94.6%

Product Performance:
Our cloud infrastructure services continued to be the primary growth driver, contributing 62% of total revenue. The newly launched AI-powered analytics platform exceeded expectations, generating $3.2M in its first full quarter. Mobile application downloads increased by 45%, with monthly active users reaching 1.2 million.

Market Expansion:
The Asian market expansion strategy yielded impressive results, with regional revenue growing 156% quarter-over-quarter. We established new offices in Singapore and Tokyo, and formed strategic partnerships with local technology providers. The European market remained stable, contributing 28% of total revenue.

Challenges and Opportunities:
While overall performance was strong, we faced challenges in supply chain management, resulting in delayed product deliveries in certain regions. The competitive landscape intensified with new entrants in the mid-market segment. However, our investment in R&D positions us well for future growth, with three major product launches planned for Q1 2024.

Outlook:
Based on current market conditions and pipeline strength, we project Q1 2024 revenue between $48M and $52M. Key focus areas include enhancing our AI capabilities, expanding the partner ecosystem, and improving operational efficiency through automation.`,
    },
    {
      title: 'News Article',
      description: 'Current events or news story',
      text: `Tech Giants Report Mixed Earnings as AI Investments Surge

Major technology companies released their quarterly earnings reports this week, revealing a complex picture of massive artificial intelligence investments coupled with varying financial performance across different sectors of the industry.

Apple reported revenue of $89.5 billion, slightly below analyst expectations, as iPhone sales in China faced increased competition from local manufacturers. However, the company's services division showed strong growth, with subscription revenue reaching an all-time high. CEO Tim Cook emphasized the company's commitment to integrating AI features across its product lineup, announcing a $10 billion investment in AI research and development over the next two years.

Microsoft exceeded Wall Street expectations with cloud revenue growing 28% year-over-year, driven largely by demand for AI services through its Azure platform. The company's partnership with OpenAI continues to pay dividends, with enterprise customers rapidly adopting AI-powered tools for productivity and development. Microsoft's gaming division also showed improvement, with Xbox Game Pass subscriptions surpassing 35 million users.

Google's parent company Alphabet reported advertising revenue growth of 11%, a recovery from previous quarters but still below pre-pandemic growth rates. The company's AI initiatives, including the Bard chatbot and various machine learning tools, are beginning to generate meaningful revenue, though specific figures were not disclosed. YouTube's revenue growth accelerated, benefiting from AI-driven recommendation improvements.

Amazon's earnings painted a more cautious picture, with the e-commerce giant warning of softer consumer spending in the coming months. However, Amazon Web Services (AWS) remained a bright spot, with revenue growing 19% as businesses continued their digital transformation efforts. The company announced plans to invest heavily in generative AI capabilities for both AWS and its consumer-facing products.

The earnings reports collectively highlight a significant shift in the technology industry, with companies prioritizing AI development even at the expense of short-term profitability. Analysts note that while these investments may pressure margins in the near term, they are essential for maintaining competitive advantage in an rapidly evolving technological landscape.`,
    },
  ];

  // Computed values
  wordCount = computed(() => {
    const text = this.inputText().trim();
    return text ? text.split(/\s+/).length : 0;
  });

  canSummarize = computed(() => {
    return this.wordCount() >= 50 && !this.summarizing();
  });

  compressionRatio = computed(() => {
    const summary = this.summary();
    if (!summary) return 0;

    const originalWords = this.wordCount();
    const summaryWords = summary.wordCount;

    if (originalWords === 0) return 0;
    return Math.round(((originalWords - summaryWords) / originalWords) * 100);
  });

  useExample(example: { title: string; description: string; text: string }) {
    this.inputText.set(example.text);
    this.showError.set(false);
  }

  clearText() {
    this.inputText.set('');
    this.showError.set(false);
  }

  summarizeText() {
    if (!this.canSummarize()) {
      this.showError.set(true);
      return;
    }

    this.summarizing.set(true);
    this.error.set(null);
    this.showError.set(false);

    const options = new SummaryOptions(this.selectedStyle());
    const filename = `text_summary_${Date.now()}.txt`;

    this.summaryService
      .createForText(this.inputText(), filename, options)
      .subscribe({
        next: (summary) => {
          this.summary.set(summary);
          this.summarizing.set(false);
          this.success.set(true);
        },
        error: (err) => {
          this.summarizing.set(false);
          this.error.set(err.message || 'Failed to generate summary');
        },
      });
  }

  copyToClipboard() {
    const summary = this.summary();
    if (!summary) return;

    navigator.clipboard.writeText(summary.content).then(() => {
      this.copied.set(true);
      setTimeout(() => this.copied.set(false), 2000);
    });
  }

  summarizeAnother() {
    this.inputText.set('');
    this.summary.set(null);
    this.success.set(false);
    this.error.set(null);
    this.selectedStyle.set(SummaryStyle.BALANCED);
  }

  tryAgain() {
    this.error.set(null);
    this.summarizeText();
  }
}
