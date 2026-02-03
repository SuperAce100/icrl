/**
 * ReAct-style agent loop implementation.
 */

import { v4 as uuidv4 } from "uuid";
import type { Message, Step, StepExample, Trajectory } from "./models";
import { formatExamples, formatHistory } from "./models";
import type { Environment, LLMProvider, OnStepCallback } from "./protocols";
import type { TrajectoryRetriever } from "./retriever";

/**
 * Context for the current step, used for prompt formatting.
 */
export interface StepContext {
  goal: string;
  plan: string;
  observation: string;
  reasoning: string;
  history: Step[];
  examples: StepExample[];
}

export interface ReActLoopOptions {
  /** Template for planning prompts */
  planPrompt: string;
  /** Template for reasoning prompts */
  reasonPrompt: string;
  /** Template for action prompts */
  actPrompt: string;
  /** Maximum number of steps per episode (default: 30) */
  maxSteps?: number;
  /** Optional callback called after each step */
  onStep?: OnStepCallback;
  /** Max characters for goal in prompts */
  maxGoalChars?: number;
  /** Max characters for plan in prompts */
  maxPlanChars?: number;
  /** Max characters for observation in prompts */
  maxObsChars?: number;
  /** Max characters for reasoning in prompts */
  maxReasoningChars?: number;
}

/**
 * ReAct-style agent loop with planning, reasoning, and acting phases.
 *
 * Follows the algorithm from the ICRL paper:
 * 1. Retrieve examples and generate initial plan
 * 2. For each step: observe, retrieve examples, reason, retrieve again, act
 * 3. Continue until done or max_steps reached
 */
export class ReActLoop {
  private readonly llm: LLMProvider;
  private readonly retriever: TrajectoryRetriever;
  private readonly planPrompt: string;
  private readonly reasonPrompt: string;
  private readonly actPrompt: string;
  private readonly maxSteps: number;
  private readonly onStep?: OnStepCallback;
  private readonly maxGoalChars: number;
  private readonly maxPlanChars: number;
  private readonly maxObsChars: number;
  private readonly maxReasoningChars: number;

  constructor(
    llm: LLMProvider,
    retriever: TrajectoryRetriever,
    options: ReActLoopOptions
  ) {
    this.llm = llm;
    this.retriever = retriever;
    this.planPrompt = options.planPrompt;
    this.reasonPrompt = options.reasonPrompt;
    this.actPrompt = options.actPrompt;
    this.maxSteps = options.maxSteps ?? 30;
    this.onStep = options.onStep;
    this.maxGoalChars = options.maxGoalChars ?? 4000;
    this.maxPlanChars = options.maxPlanChars ?? 2000;
    this.maxObsChars = options.maxObsChars ?? 5000;
    this.maxReasoningChars = options.maxReasoningChars ?? 2000;
  }

  /**
   * Run a complete episode.
   */
  async run(env: Environment, goal: string): Promise<Trajectory> {
    this.retriever.clearRetrieved();

    let observation = await Promise.resolve(env.reset(goal));

    const planUsesExamples = this.planPrompt.includes("{examples}");
    const reasonUsesExamples = this.reasonPrompt.includes("{examples}");
    const actUsesExamples = this.actPrompt.includes("{examples}");

    const planExamples = planUsesExamples
      ? await this.retriever.retrieveForPlan(goal)
      : [];
    const plan = await this.generatePlan(goal, planExamples);

    const steps: Step[] = [];
    let done = false;
    let success = false;

    for (let stepNum = 0; stepNum < this.maxSteps; stepNum++) {
      const context: StepContext = {
        goal,
        plan,
        observation,
        reasoning: "",
        history: [...steps],
        examples: [],
      };

      if (reasonUsesExamples || actUsesExamples) {
        context.examples = await this.retriever.retrieveForStep(goal, plan, observation);
      }

      const reasoning = await this.generateReasoning(context);
      context.reasoning = reasoning;

      const action = await this.generateAction(context);

      const step: Step = {
        observation,
        reasoning,
        action,
      };
      steps.push(step);

      if (this.onStep) {
        this.onStep(step, { goal, plan, stepNumber: stepNum + 1 });
      }

      const result = await Promise.resolve(env.step(action));
      observation = result.observation;
      done = result.done;
      success = result.success;

      if (done) break;
    }

    this.retriever.recordEpisodeResult(success);

    return {
      id: uuidv4(),
      goal,
      plan,
      steps,
      success,
      metadata: {},
    };
  }

  private async generatePlan(goal: string, examples: StepExample[]): Promise<string> {
    const context: StepContext = {
      goal,
      plan: "",
      observation: "",
      reasoning: "",
      history: [],
      examples,
    };
    const prompt = this.formatPrompt(this.planPrompt, context);
    const messages: Message[] = [{ role: "user", content: prompt }];
    return this.llm.complete(messages);
  }

  private async generateReasoning(context: StepContext): Promise<string> {
    const prompt = this.formatPrompt(this.reasonPrompt, context);
    const messages: Message[] = [{ role: "user", content: prompt }];
    return this.llm.complete(messages);
  }

  private async generateAction(context: StepContext): Promise<string> {
    const prompt = this.formatPrompt(this.actPrompt, context);
    const messages: Message[] = [{ role: "user", content: prompt }];
    return this.llm.complete(messages);
  }

  private formatPrompt(template: string, context: StepContext): string {
    const cap = (text: string, limit: number): string => {
      if (limit <= 0) return "";
      if (text.length <= limit) return text;
      return text.slice(0, limit) + "\n...[truncated]...";
    };

    return template
      .replace("{goal}", cap(context.goal, this.maxGoalChars))
      .replace("{plan}", cap(context.plan, this.maxPlanChars))
      .replace("{observation}", cap(context.observation, this.maxObsChars))
      .replace("{reasoning}", cap(context.reasoning, this.maxReasoningChars))
      .replace("{history}", formatHistory(context.history))
      .replace("{examples}", formatExamples(context.examples));
  }
}
