# Subsystem Checklist

Use this checklist during investigation.

## Repo and Build

- Root scripts and primary dev path
- Workspace/package boundaries
- Shared vs duplicated tool configs

## Storybook

- Number and location of `.storybook` configs
- Story source aggregation and ownership
- Story size hotspots and monolith files

## Runtime Shell and Windowing

- Shell orchestration responsibilities
- Window lifecycle and interaction flow
- High-frequency drag/resize update path
- Memoization and render isolation strategy

## State Management

- Store factory and reducer composition
- Selector patterns and invalidation risks
- High-frequency event dispatch impact

## Chat/Timeline/Event Pipeline

- Transport/client boundary
- Envelope parsing/projection layering
- Reducer responsibilities and coupling
- Debug/event-view path and storage strategy

## Plugin Runtime

- Session lifecycle
- Runtime card injection path
- Unused/ambiguous exported surfaces

## CSS/Theming/Design System

- Token and part architecture
- CSS file layout and modularity
- Inline-style usage in runtime components
- Theming/extensibility readiness

## Duplication/Deprecation

- Repeated helpers/patterns
- Legacy or marked-unused files
- Ambiguous APIs that need status decisions
