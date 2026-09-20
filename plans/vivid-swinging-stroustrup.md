# Implementation Plan: Enhancing FloodRoute Frontend

## Context
The goal is to enhance the FloodRoute frontend to be a polished, modern navigation application. Key improvements include enabling worldwide search (removing Indian-only restriction), improving search result ranking and UI, beautifying the map interactions, and making the flooding reporting flow seamless.

## Critical Files to Modify
- `frontend/src/services/geocoding.js`: Remove `countrycodes: 'in'`, refine `isUsefulPlace` and `rankPlace` for worldwide support.
- `frontend/src/components/SearchPanel.jsx`: Implement modern search UI (debouncing, loading state, refined display).
- `frontend/src/components/MapView.jsx`: Beautify markers, popups, and route displays.
- `frontend/src/components/RouteRiskCard.jsx`: Update risk labeling and explanation.
- `frontend/src/components/ReportForm.jsx`: Streamline report flooding flow.
- `frontend/src/App.css` / Component CSS files: General styling improvements.

## Implementation Steps

### 1. Worldwide Search & Ranking
- Modify `geocode` in `frontend/src/services/geocoding.js` to remove `countrycodes: 'in'`.
- Review and refine `isUsefulPlace` and `rankPlace` to ensure better ranking for cities/towns over specific buildings worldwide.
- Add robust error handling for geocoding failures.

### 2. Modern Search UI
- Implement debouncing in `SearchPanel.jsx`.
- Display a cleaner list of results with place type badges.
- Add visual indicators for loading / error states in search.

### 3. Beautification
- Standardize map marker styling and popup content.
- Enhance accessibility (ARIA labels, focus states).
- Improve overall component styling in CSS files for a modern, navigation-focused feel.

### 4. Risk & Report UX
- Consolidate risk categorization terminology.
- Streamline the flooding report capture flow.

## Verification Plan
1. **End-to-End Search Test**: Verify worldwide search works (e.g., London, New York) and India-specific search still works.
2. **Ranking Test**: Ensure cities/towns are prioritized over specific buildings in search results.
3. **Route Risk Test**: Validating the API contract remains intact after frontend changes.
4. **UI Verification**: Run the app locally and perform a visual check of the improved components, responsive behavior, and accessibility.
5. **Build Check**: Ensure `npm run build` completes successfully.
