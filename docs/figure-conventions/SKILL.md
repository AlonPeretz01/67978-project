---
name: python-data-visualization
description: >
  Standards for creating, modifying, reviewing, or debugging data visualizations in Python.
  MUST be used whenever a task creates or changes charts, plots, figures, dashboards, EDA visualizations,
  or publication-ready graphics with matplotlib, seaborn, plotly, pandas plotting, or similar Python libraries.
---

# Python Data Visualization Standards

Use these rules whenever producing a visualization in Python.

## 1. Start with the analytical question

Before plotting, identify what the visualization is meant to do:
- reveal a pattern,
- compare groups,
- show a distribution,
- communicate a takeaway,
- expose possible data problems.

Choose the simplest visual encoding that answers that question.

## 2. Scale and axes

- Choose axis limits that reveal the data rather than hide it.
- Keep an axis scale consistent; never change scale midway through an axis.
- Do not use different scales for the same visual axis in a way that creates a misleading comparison.
- If most observations occupy a small region, zoom into that region or create a separate plot for it.
- When comparing multiple plots, use common axis limits when direct visual comparison matters.
- Clearly indicate any transformation or non-standard scale.

## 3. Conditioning and subgroup comparisons

When an overall plot hides structure:
- split or facet by relevant subgroups,
- align comparable groups on the same scale,
- prefer small multiples when they make differences easier to compare.

Do not rely on a single aggregated plot when subgroup structure is important.

## 4. Perception and visual encoding

Prefer encodings humans judge accurately.

Order of preference for quantitative comparison:
1. position on a common scale,
2. length,
3. position on separate but aligned scales,
4. angle or area only when necessary.

Practical rules:
- Prefer bar charts over pie charts for comparing quantities.
- Avoid pie charts when accurate comparison matters; angle judgments are difficult.
- Avoid area-based charts when the viewer must compare precise magnitudes.
- Avoid word clouds for quantitative comparison; word length and font area distort perceived frequency.
- Avoid stacked bars or stacked area charts when comparison of non-baseline segments is important, because their baselines move.
- Prefer separate lines or small multiples when stacked displays obscure comparison.

## 5. Color

- Use color to encode meaning, not decoration.
- Prefer perceptually uniform colormaps such as `viridis` for ordered numeric data.
- Do not use `jet` / rainbow colormaps for quantitative values.
- Avoid red-vs-green as the only distinction because of common color-vision deficiencies.
- For values with a meaningful center where both low and high values deserve emphasis, use a diverging palette with a light/neutral midpoint.
- Keep category colors stable across related figures.
- Do not use more distinct colors than the viewer can reasonably track; facet or label instead when categories become numerous.

## 6. Transformations

Transform data when it reveals structure that the original scale hides.

Examples:
- For heavy-tailed distributions, consider a log transform.
- For nonlinear relationships, consider plotting one or both variables on a log scale.

Whenever a transformation is used:
- make it explicit in the axis label or caption,
- do not present transformed values as if they were raw values.

## 7. Overplotting and smoothing

When many observations overlap:
- reduce marker size,
- use transparency,
- consider hexbin/density displays,
- facet into meaningful groups,
- or add a smoothing/trend line when the goal is to expose the overall pattern.

Smoothing must clarify the data, not replace it. Keep raw observations visible when practical.

## 8. Context: make shared figures self-explanatory

A publication-ready figure should include:
- an informative title that states the takeaway rather than merely naming the chart,
- clear x- and y-axis labels,
- units where applicable,
- reference lines or markers for important values when useful,
- labels or annotations for unusual/important observations when useful,
- a caption when the data source, filtering, transformation, or interpretation needs explanation.

Prefer:
`Older passengers spend more on plane tickets`

over:
`Scatter plot of price vs. age`

## 9. Typography and readability

The source lecture emphasizes readability but does not prescribe exact numeric font sizes. Use these as implementation defaults unless the target medium requires otherwise.

For a standard notebook/report figure around 8×5 to 10×6 inches:
- Figure title: **16–18 pt**, semibold/bold.
- Axis labels: **13–14 pt**.
- Tick labels: **11–12 pt**.
- Legend text: **11–12 pt**.
- Annotations/data labels: **10–12 pt**, never smaller than **10 pt** for a normal exported figure.
- Caption/source text: **10–11 pt**.

For presentation/slides, scale text up substantially; no important chart text should require zooming to read.

Never solve overcrowding by shrinking text excessively. Instead:
- enlarge the figure,
- reduce the number of labels,
- facet the chart,
- rotate labels only when necessary,
- or change the visualization.

## 10. Default matplotlib baseline

Use this as a starting point, then adapt to the figure and output medium:

```python
import matplotlib.pyplot as plt

plt.rcParams.update({
    "figure.figsize": (9, 5.5),
    "figure.dpi": 120,
    "savefig.dpi": 200,
    "font.size": 12,
    "axes.titlesize": 17,
    "axes.titleweight": "semibold",
    "axes.labelsize": 13,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 11,
})
```

Do not blindly apply these values if the chart is unusually dense, unusually small, or intended for slides.

## 11. Final quality check

Before finishing a visualization, verify:

- [ ] The visual answers a clear question.
- [ ] The chosen chart type supports accurate comparison.
- [ ] Axis scales are consistent and not misleading.
- [ ] Relevant subgroup structure has not been hidden by aggregation.
- [ ] Color has a semantic purpose and is accessible.
- [ ] No rainbow/jet colormap is used for quantitative data.
- [ ] Pie/area/stacking has been avoided when a clearer positional or length encoding is available.
- [ ] Any transformation is explicit.
- [ ] Overplotting has been addressed.
- [ ] The title states the takeaway when the plot is being communicated to others.
- [ ] Axes have meaningful labels and units.
- [ ] Important reference values or unusual points are annotated when useful.
- [ ] All text is comfortably readable at the final display/export size.
- [ ] The plot reveals the data rather than decorating it.

## 12. Project-specific conventions (67978)

### Uncertainty
Every proportion must carry a Wilson 95% confidence interval, shown as error
bars. Annual response counts in this project vary by a factor of thirty-six
(2,747 in 2011 to 98,855 in 2018), so points differ enormously in precision.
A bare bar or marker implies a certainty the data does not have.

### Non-comparable measurements
Where a survey year uses a different instrument from the rest of the series
(2015, 2016 and 2025 measure general rather than professional experience),
plot those points as hollow, unconnected markers, never joined to the main
line, with a legend entry naming them as non-comparable. Connecting them would
imply a trend across measures that are not on the same scale.

### Axes
Percentage axes run 0–100 with a percent formatter, consistently across every
figure in the project, so that figures can be compared directly.

### Year facetting
When a figure covers multiple survey years, split by year rather than pooling,
unless the pooled view is itself the point. Pooling hides year-to-year movement,
which is the primary question in this project.