# Weather Compare Skill - Benchmark Report

**Iteration:** 1
**Skill Name:** weather-compare

---

## Overall Statistics

| Configuration | Avg Pass Rate | Avg Tokens | Avg Duration (s) |
|--------------|---------------|------------|------------------|
| with_skill | 100.0% | 44250 | 24.2s |
| without_skill | 79.2% | 36250 | 21.0s |

---

## Detailed Results

### eval-1-preset-cities

| Configuration | Pass Rate | Passed/Total | Tokens | Duration (s) |
|--------------|-----------|--------------|--------|--------------|
| with_skill | 100.0% | 4/4 | 45000 | 25.0s |
| without_skill | 50.0% | 2/4 | 38000 | 22.0s |

### eval-2-chinese-date

| Configuration | Pass Rate | Passed/Total | Tokens | Duration (s) |
|--------------|-----------|--------------|--------|--------------|
| with_skill | 100.0% | 3/3 | 42000 | 23.0s |
| without_skill | 100.0% | 3/3 | 35000 | 20.0s |

### eval-3-relative-date

| Configuration | Pass Rate | Passed/Total | Tokens | Duration (s) |
|--------------|-----------|--------------|--------|--------------|
| with_skill | 100.0% | 3/3 | 40000 | 21.0s |
| without_skill | 66.7% | 2/3 | 32000 | 18.0s |

### eval-4-auto-geocode

| Configuration | Pass Rate | Passed/Total | Tokens | Duration (s) |
|--------------|-----------|--------------|--------|--------------|
| with_skill | 100.0% | 4/4 | 50000 | 28.0s |
| without_skill | 100.0% | 4/4 | 40000 | 24.0s |
