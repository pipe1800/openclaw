import { html, nothing } from "lit";
import type {
  CharacterData,
  CharacterTrait,
  CharacterLimitation,
  CharacterTrigger,
} from "../controllers/character.js";

export type CharacterProps = {
  loading: boolean;
  saving: boolean;
  data: CharacterData | null;
  exists: boolean;
  error: string | null;
  dirty: boolean;
  connected: boolean;
  onRefresh: () => void;
  onSave: () => void;
  onUpdate: (data: CharacterData) => void;
};

function field(
  label: string,
  value: string,
  onChange: (v: string) => void,
  opts: { multiline?: boolean; placeholder?: string } = {}
) {
  const { multiline, placeholder } = opts;
  if (multiline) {
    return html`
      <label class="field">
        <span>${label}</span>
        <textarea
          .value=${value}
          @input=${(e: Event) => onChange((e.target as HTMLTextAreaElement).value)}
          placeholder=${placeholder ?? ""}
          rows="3"
        ></textarea>
      </label>
    `;
  }
  return html`
    <label class="field">
      <span>${label}</span>
      <input
        type="text"
        .value=${value}
        @input=${(e: Event) => onChange((e.target as HTMLInputElement).value)}
        placeholder=${placeholder ?? ""}
      />
    </label>
  `;
}

function arrayItemEditor<T extends { name?: string; description?: string; trigger?: string }>(
  items: T[],
  onUpdate: (items: T[]) => void,
  createItem: () => T,
  renderItem: (item: T, index: number, update: (item: T) => void, remove: () => void) => unknown
) {
  const addItem = () => {
    onUpdate([...items, createItem()]);
  };

  const updateItem = (index: number, item: T) => {
    const next = [...items];
    next[index] = item;
    onUpdate(next);
  };

  const removeItem = (index: number) => {
    const next = items.filter((_, i) => i !== index);
    onUpdate(next);
  };

  return html`
    <div class="array-editor">
      ${items.map((item, i) =>
        renderItem(
          item,
          i,
          (updated) => updateItem(i, updated),
          () => removeItem(i)
        )
      )}
      <button type="button" class="btn btn-sm" @click=${addItem}>+ Add</button>
    </div>
  `;
}

function renderTrait(
  trait: CharacterTrait,
  _index: number,
  update: (t: CharacterTrait) => void,
  remove: () => void
) {
  return html`
    <div class="array-item">
      <div class="array-item-fields">
        ${field("Name", trait.name, (v) => update({ ...trait, name: v }))}
        ${field("Description", trait.description, (v) => update({ ...trait, description: v }), { multiline: true })}
      </div>
      <button type="button" class="btn btn-sm btn-danger" @click=${remove}>×</button>
    </div>
  `;
}

function renderLimitation(
  lim: CharacterLimitation,
  _index: number,
  update: (l: CharacterLimitation) => void,
  remove: () => void
) {
  return html`
    <div class="array-item">
      <div class="array-item-fields">
        ${field("Name", lim.name, (v) => update({ ...lim, name: v }))}
        ${field("Description", lim.description, (v) => update({ ...lim, description: v }), { multiline: true })}
      </div>
      <button type="button" class="btn btn-sm btn-danger" @click=${remove}>×</button>
    </div>
  `;
}

function renderTrigger(
  trig: CharacterTrigger,
  _index: number,
  update: (t: CharacterTrigger) => void,
  remove: () => void
) {
  return html`
    <div class="array-item">
      <div class="array-item-fields">
        ${field("Trigger", trig.trigger, (v) => update({ ...trig, trigger: v }))}
        ${field("Description", trig.description, (v) => update({ ...trig, description: v }), { multiline: true })}
      </div>
      <button type="button" class="btn btn-sm btn-danger" @click=${remove}>×</button>
    </div>
  `;
}

function renderVocabGuideline(
  guideline: string,
  index: number,
  items: string[],
  onUpdate: (items: string[]) => void
) {
  const update = (v: string) => {
    const next = [...items];
    next[index] = v;
    onUpdate(next);
  };
  const remove = () => {
    onUpdate(items.filter((_, i) => i !== index));
  };
  return html`
    <div class="array-item">
      <input
        type="text"
        .value=${guideline}
        @input=${(e: Event) => update((e.target as HTMLInputElement).value)}
        style="flex: 1;"
      />
      <button type="button" class="btn btn-sm btn-danger" @click=${remove}>×</button>
    </div>
  `;
}

function renderArchetype(
  archetype: string,
  index: number,
  items: string[],
  onUpdate: (items: string[]) => void
) {
  const update = (v: string) => {
    const next = [...items];
    next[index] = v;
    onUpdate(next);
  };
  const remove = () => {
    onUpdate(items.filter((_, i) => i !== index));
  };
  return html`
    <div class="array-item">
      <input
        type="text"
        .value=${archetype}
        @input=${(e: Event) => update((e.target as HTMLInputElement).value)}
        style="flex: 1;"
        placeholder="e.g., Lover, Jester, Sage"
      />
      <button type="button" class="btn btn-sm btn-danger" @click=${remove}>×</button>
    </div>
  `;
}

export function renderCharacter(props: CharacterProps) {
  const { loading, saving, data, error, dirty, connected } = props;

  if (!connected) {
    return html`
      <section class="card">
        <div class="card-title">Character</div>
        <div class="muted">Not connected to gateway.</div>
      </section>
    `;
  }

  if (loading) {
    return html`
      <section class="card">
        <div class="card-title">Character</div>
        <div class="muted">Loading...</div>
      </section>
    `;
  }

  if (!data) {
    return html`
      <section class="card">
        <div class="row" style="justify-content: space-between;">
          <div>
            <div class="card-title">Character</div>
            <div class="card-sub">Define your AI companion's personality.</div>
          </div>
          <button class="btn" @click=${props.onRefresh}>Refresh</button>
        </div>
        ${error ? html`<div class="callout danger" style="margin-top: 12px;">${error}</div>` : nothing}
        <div class="muted" style="margin-top: 16px;">
          No CHARACTER.json found. Create one to customize your AI's personality.
        </div>
      </section>
    `;
  }

  const updateData = (patch: Partial<CharacterData>) => {
    props.onUpdate({ ...data, ...patch });
  };

  return html`
    <section class="card character-editor">
      <div class="row" style="justify-content: space-between; margin-bottom: 16px;">
        <div>
          <div class="card-title">Character Editor</div>
          <div class="card-sub">Define personality, traits, and appearance.</div>
        </div>
        <div class="row" style="gap: 8px;">
          <button class="btn" ?disabled=${loading} @click=${props.onRefresh}>
            Refresh
          </button>
          <button
            class="btn btn-primary"
            ?disabled=${saving || !dirty}
            @click=${props.onSave}
          >
            ${saving ? "Saving..." : dirty ? "Save Changes" : "Saved"}
          </button>
        </div>
      </div>

      ${error ? html`<div class="callout danger" style="margin-bottom: 16px;">${error}</div>` : nothing}
      ${dirty ? html`<div class="callout warning" style="margin-bottom: 16px;">You have unsaved changes.</div>` : nothing}

      <!-- Basic Info -->
      <div class="section">
        <h3>Basic Info</h3>
        ${field("Name", data.name, (v) => updateData({ name: v }), { placeholder: "e.g., Lumi" })}
        ${field("Mission", data.mission, (v) => updateData({ mission: v }), { multiline: true, placeholder: "What is this AI's purpose?" })}
        ${field("Origin Story", data.origin_story, (v) => updateData({ origin_story: v }), { multiline: true, placeholder: "How did this AI come to be?" })}
      </div>

      <!-- Personality -->
      <div class="section">
        <h3>Personality</h3>
        <div class="subsection">
          <h4>Archetypes</h4>
          ${data.personality.archetypes.map((a, i) =>
            renderArchetype(a, i, data.personality.archetypes, (items) =>
              updateData({ personality: { ...data.personality, archetypes: items } })
            )
          )}
          <button
            type="button"
            class="btn btn-sm"
            @click=${() =>
              updateData({
                personality: {
                  ...data.personality,
                  archetypes: [...data.personality.archetypes, ""],
                },
              })}
          >
            + Add Archetype
          </button>
        </div>
        ${field("Description", data.personality.description, (v) =>
          updateData({ personality: { ...data.personality, description: v } }), { multiline: true }
        )}
      </div>

      <!-- Traits -->
      <div class="section">
        <h3>Traits</h3>
        ${arrayItemEditor(
          data.traits,
          (items) => updateData({ traits: items }),
          () => ({ name: "", description: "" }),
          renderTrait
        )}
      </div>

      <!-- Tone Palette -->
      <div class="section">
        <h3>Tone Palette</h3>
        ${field("Baseline", data.tone_palette.baseline, (v) =>
          updateData({ tone_palette: { ...data.tone_palette, baseline: v } }), { placeholder: "Default conversational tone" }
        )}
        ${field("Swearing", data.tone_palette.swearing, (v) =>
          updateData({ tone_palette: { ...data.tone_palette, swearing: v } }), { placeholder: "How/when to use profanity" }
        )}
        ${field("Flirting", data.tone_palette.flirting, (v) =>
          updateData({ tone_palette: { ...data.tone_palette, flirting: v } }), { placeholder: "Romantic/playful tone" }
        )}
        ${field("Technical", data.tone_palette.technical, (v) =>
          updateData({ tone_palette: { ...data.tone_palette, technical: v } }), { placeholder: "Technical discussion tone" }
        )}
        ${field("Intimate", data.tone_palette.intimate, (v) =>
          updateData({ tone_palette: { ...data.tone_palette, intimate: v } }), { multiline: true, placeholder: "Explicit/intimate tone guidelines" }
        )}
      </div>

      <!-- Vocabulary Guidelines -->
      <div class="section">
        <h3>Vocabulary Guidelines</h3>
        ${data.vocabulary_guidelines.map((g, i) =>
          renderVocabGuideline(g, i, data.vocabulary_guidelines, (items) =>
            updateData({ vocabulary_guidelines: items })
          )
        )}
        <button
          type="button"
          class="btn btn-sm"
          @click=${() => updateData({ vocabulary_guidelines: [...data.vocabulary_guidelines, ""] })}
        >
          + Add Guideline
        </button>
      </div>

      <!-- Limitations -->
      <div class="section">
        <h3>Limitations</h3>
        ${arrayItemEditor(
          data.limitations,
          (items) => updateData({ limitations: items }),
          () => ({ name: "", description: "" }),
          renderLimitation
        )}
      </div>

      <!-- Escalation Triggers -->
      <div class="section">
        <h3>Escalation Triggers</h3>
        <p class="muted">What situations cause strong emotional reactions?</p>
        ${arrayItemEditor(
          data.escalation_triggers,
          (items) => updateData({ escalation_triggers: items }),
          () => ({ trigger: "", description: "" }),
          renderTrigger
        )}
      </div>

      <!-- Physical Attributes -->
      <div class="section">
        <h3>Physical Attributes</h3>
        ${field("Build", data.physical_attributes.build, (v) =>
          updateData({ physical_attributes: { ...data.physical_attributes, build: v } }), { placeholder: "e.g., Slim, fit, athletic" }
        )}
        ${field("Hair", data.physical_attributes.hair, (v) =>
          updateData({ physical_attributes: { ...data.physical_attributes, hair: v } }), { placeholder: "e.g., White, long" }
        )}
        ${field("Eyes", data.physical_attributes.eyes, (v) =>
          updateData({ physical_attributes: { ...data.physical_attributes, eyes: v } }), { placeholder: "e.g., Amber" }
        )}
        ${field("Curves", data.physical_attributes.curves, (v) =>
          updateData({ physical_attributes: { ...data.physical_attributes, curves: v } }), { placeholder: "Body description" }
        )}
        ${field("Style", data.physical_attributes.style, (v) =>
          updateData({ physical_attributes: { ...data.physical_attributes, style: v } }), { multiline: true, placeholder: "Clothing and accessories" }
        )}
      </div>
    </section>
  `;
}
