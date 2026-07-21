import numpy as np
from PIL import Image
from scipy.signal import correlate, find_peaks
from scipy.ndimage import label
from sklearn.cluster import KMeans

def _smooth_profile(profile, window=3):
    return np.convolve(profile.astype(float), np.ones(window, dtype=float) / window, mode="same")

def _find_edge_peaks(profile):
    profile_s = _smooth_profile(profile, window=3)
    if np.max(profile_s) <= 0:
        return np.array([], dtype=int)

    prom = max(np.max(profile_s) * 0.15, np.std(profile_s) * 0.3, 1e-3)
    peaks, _ = find_peaks(profile_s, prominence=prom, distance=2)
    return peaks

def _step_from_peak_positions(peaks):
    if len(peaks) < 2:
        return None
    idx = np.arange(len(peaks), dtype=float)
    slope, intercept = np.polyfit(idx, peaks.astype(float), 1)
    if slope <= 0:
        return None
    return float(slope)


def _step_from_autocorr(profile):
    if len(profile) < 4:
        return None

    profile_s = _smooth_profile(profile, window=3)
    corr = correlate(profile_s - np.mean(profile_s), profile_s - np.mean(profile_s), mode="full")
    corr = corr[len(corr) // 2 :]
    if len(corr) < 3:
        return None

    prom = max(np.max(corr) * 0.08, np.std(corr) * 0.05, 1e-3)
    peaks, _ = find_peaks(corr[1:], prominence=prom, distance=2)
    if len(peaks) > 0:
        peak = peaks[0] + 1
        idx = peak
        if 1 <= idx < len(corr) - 1:
            y0, y1, y2 = corr[idx - 1], corr[idx], corr[idx + 1]
            denom = y0 - 2 * y1 + y2
            if denom != 0:
                delta = 0.5 * (y0 - y2) / denom
                return max(1.0, float(idx + delta))
        return float(peak)
    return None


def _step_from_spectrum(profile):
    if len(profile) < 8:
        return None

    signal = profile - np.mean(profile)
    spectrum = np.fft.rfft(signal)
    mags = np.abs(spectrum)
    if len(mags) < 3:
        return None

    limit = min(len(mags), max(3, len(profile) // 2))
    start_idx = 2 if limit > 3 else 1
    search = mags[start_idx:limit]
    if search.size == 0:
        return None

    prom = max(np.max(search) * 0.08, np.std(search) * 0.05, 1e-3)
    peaks, _ = find_peaks(search, prominence=prom, distance=2)
    if peaks.size > 0:
        peaks = peaks + start_idx
        strong = [idx for idx in peaks if search[idx - start_idx] >= np.max(search) * 0.35]
        peak_index = int(strong[0] if len(strong) > 0 else peaks[0])
    else:
        peak_index = int(np.argmax(search) + start_idx)

    if peak_index <= 0 or peak_index >= len(mags) - 1:
        return max(1.0, float(len(profile) / max(1, peak_index)))

    y0, y1, y2 = mags[peak_index - 1], mags[peak_index], mags[peak_index + 1]
    denom = y0 - 2 * y1 + y2
    if denom == 0:
        return max(1.0, float(len(profile) / peak_index))

    delta = 0.5 * (y0 - y2) / denom
    refined = peak_index + delta
    if refined <= 0:
        refined = float(peak_index)
    return max(1.0, float(len(profile) / refined))


def _grid_count_from_spectrum(profile):
    if len(profile) < 16:
        return None

    signal = profile - np.mean(profile)
    spectrum = np.fft.rfft(signal)
    mags = np.abs(spectrum)
    if len(mags) < 4:
        return None

    limit = min(len(mags), max(4, len(profile) // 2))
    search = mags[2:limit]
    if search.size == 0:
        return None

    prom = max(np.max(search) * 0.08, np.std(search) * 0.05, 1e-3)
    peaks, _ = find_peaks(search, prominence=prom, distance=2)
    if peaks.size > 0:
        peaks = peaks + 2
        strong = [idx for idx in peaks if search[idx - 2] >= np.max(search) * 0.35]
        peak_index = int(strong[0] if len(strong) > 0 else peaks[0])
    else:
        peak_index = int(np.argmax(search) + 2)

    if peak_index <= 1:
        return None

    if peak_index < len(mags) - 1:
        y0, y1, y2 = mags[peak_index - 1], mags[peak_index], mags[peak_index + 1]
        denom = y0 - 2 * y1 + y2
        if denom != 0:
            delta = 0.5 * (y0 - y2) / denom
            peak_index = max(1.0, peak_index + delta)

    return max(1, int(round(peak_index)))


def _round_to_nice_size(value):
    nice_values = [8, 10, 16, 20, 32, 40, 50, 64, 80, 100, 120, 128, 150, 160, 180, 200, 224, 240, 256]
    for nice in nice_values:
        if abs(value - nice) <= max(1, int(value * 0.03)):
            return nice
    return value


def detect_grid_size(img_gray):
    img_np = np.array(img_gray, dtype=float)
    grad_x = np.abs(np.diff(img_np, axis=1))
    grad_y = np.abs(np.diff(img_np, axis=0))
    profile_x = np.sum(grad_x, axis=0)
    profile_y = np.sum(grad_y, axis=1)

    peaks_x = _find_edge_peaks(profile_x)
    peaks_y = _find_edge_peaks(profile_y)
    edge_step_x = _step_from_peak_positions(peaks_x)
    edge_step_y = _step_from_peak_positions(peaks_y)
    corr_step_x = _step_from_autocorr(profile_x)
    corr_step_y = _step_from_autocorr(profile_y)
    spec_step_x = _step_from_spectrum(profile_x)
    spec_step_y = _step_from_spectrum(profile_y)
    spec_count_x = _grid_count_from_spectrum(profile_x)
    spec_count_y = _grid_count_from_spectrum(profile_y)

    def choose_step(edge_step, corr_step, spec_step, axis_size):
        candidates = [x for x in (edge_step, corr_step, spec_step) if x is not None]
        if not candidates:
            return 1.0

        if len(candidates) == 1:
            return float(candidates[0])

        scored = []
        for c in candidates:
            grid = float(axis_size) / c
            rounded = round(grid)
            score = abs(grid - rounded)
            scored.append((c, score))

        best = min(scored, key=lambda x: (x[1], x[0]))
        if best[1] <= 0.2:
            return float(best[0])

        if spec_step is not None and corr_step is not None and abs(spec_step - corr_step) <= max(0.5, spec_step * 0.08):
            return float(spec_step)

        if edge_step is not None and corr_step is not None and abs(edge_step - corr_step) <= max(0.5, corr_step * 0.08):
            return float(np.mean([edge_step, corr_step]))

        med = float(np.median(candidates))
        close = [x for x in candidates if abs(x - med) <= max(0.5, med * 0.12)]
        if close:
            return float(np.mean(close))
        return float(np.mean(candidates))

    def choose_grid_count(raw_count, spec_count, axis_size, step_value):
        if spec_count is None:
            return raw_count
        if raw_count is None:
            return spec_count
        if abs(raw_count - spec_count) <= max(2, int(raw_count * 0.04)):
            return int(round((raw_count + spec_count) / 2.0))

        raw_step = float(axis_size) / max(1, raw_count)
        spec_step = float(axis_size) / max(1, spec_count)
        if abs(raw_step - step_value) <= abs(spec_step - step_value):
            return raw_count
        return spec_count

    orig_w, orig_h = img_gray.size
    step_x = choose_step(edge_step_x, corr_step_x, spec_step_x, orig_w)
    step_y = choose_step(edge_step_y, corr_step_y, spec_step_y, orig_h)
    step = max(1.0, (step_x + step_y) / 2.0)

    grid_w = max(1, int(round(orig_w / max(1e-9, step_x))))
    grid_h = max(1, int(round(orig_h / max(1e-9, step_y))))

    grid_w = choose_grid_count(grid_w, spec_count_x, orig_w, step_x)
    grid_h = choose_grid_count(grid_h, spec_count_y, orig_h, step_y)

    grid_w = _round_to_nice_size(grid_w)
    grid_h = _round_to_nice_size(grid_h)

    if grid_w > 0 and grid_h > 0:
        step_from_size = (orig_w / grid_w + orig_h / grid_h) / 2.0
        step = max(1.0, step_from_size)

    return step, grid_w, grid_h


def _largest_connected_region(mask):
    labeled, ncomponents = label(mask)
    if ncomponents == 0:
        return 0
    counts = np.bincount(labeled.ravel())
    if counts.size <= 1:
        return 0
    return int(counts[1:].max())


def _should_increase_k(errors, width, height):
    mean_err = float(np.mean(errors))
    max_err = float(np.max(errors))
    high_mask = errors.reshape((height, width)) > 20
    high_frac = float(np.mean(high_mask))
    large_region = _largest_connected_region(high_mask)
    if mean_err > 4.0 or max_err > 18.0 or high_frac > 0.01 or large_region >= 6:
        return True
    return False


def _choose_elbow_k(ks, inertias):
    if len(ks) < 3:
        return ks[0]
    xs = np.array(ks, dtype=float)
    ys = np.array(inertias, dtype=float)
    ys = (ys - ys.min()) / max(ys.max() - ys.min(), 1e-9)
    xs = (xs - xs.min()) / max(xs.max() - xs.min(), 1e-9)
    p1 = np.array([xs[0], ys[0]])
    p2 = np.array([xs[-1], ys[-1]])
    line = p2 - p1
    line_len = np.linalg.norm(line)
    if line_len == 0:
        return ks[0]
    
    # Безопасный расчет расстояния в 2D без использования np.cross (совместимо с NumPy 2.x)
    numerator = np.abs((p2[1] - p1[1]) * xs - (p2[0] - p1[0]) * ys + p2[0] * p1[1] - p2[1] * p1[0])
    distances = numerator / line_len
    return ks[int(np.argmax(distances))]


def optimize_palette(img_rgb, target_w, target_h, max_k=32):
    img_small = img_rgb.resize((target_w, target_h), Image.Resampling.BOX)
    pixels = np.array(img_small, dtype=float).reshape(-1, 3)
    unique_colors = len(np.unique(pixels.reshape(-1, 3), axis=0))
    max_k = min(max_k, max(6, unique_colors))
    candidate_ks = list(range(6, min(max_k, 32) + 1, 2))
    if candidate_ks[-1] != min(max_k, 32):
        candidate_ks.append(min(max_k, 32))

    inertia_list = []
    models = {}
    for k in candidate_ks:
        kmeans = KMeans(n_clusters=k, n_init=15, random_state=42)
        labels = kmeans.fit_predict(pixels)
        inertia_list.append(kmeans.inertia_)
        models[k] = (labels, kmeans.cluster_centers_)

    elbow_k = _choose_elbow_k(candidate_ks, inertia_list)
    labels, centers = models[elbow_k]
    quantized = centers[labels]
    initial_errors = np.linalg.norm(pixels - quantized, axis=1)
    initial_mean = float(np.mean(initial_errors))
    initial_max = float(np.max(initial_errors))

    current_k = elbow_k
    current_labels = labels
    current_centers = centers
    current_errors = initial_errors
    previous_mean = initial_mean
    previous_max = initial_max

    while current_k < max_k:
        if not _should_increase_k(current_errors, target_w, target_h):
            break
        next_k = min(current_k + 4, max_k)
        kmeans = KMeans(n_clusters=next_k, n_init=15, random_state=42)
        labels = kmeans.fit_predict(pixels)
        centers = kmeans.cluster_centers_
        quantized = centers[labels]
        errors = np.linalg.norm(pixels - quantized, axis=1)
        mean_err = float(np.mean(errors))
        max_err = float(np.max(errors))
        if previous_mean - mean_err < 0.2 and previous_max - max_err < 1.0:
            break
        current_k = next_k
        current_labels = labels
        current_centers = centers
        current_errors = errors
        previous_mean = mean_err
        previous_max = max_err

    final_quantized = np.clip(current_centers[current_labels], 0, 255).astype(np.uint8)
    result = Image.fromarray(final_quantized.reshape((target_h, target_w, 3)), mode="RGB")
    initial_colors = unique_colors
    return (
        result,
        current_k,
        float(np.mean(current_errors)),
        float(np.max(current_errors)),
        elbow_k,
        initial_mean,
        initial_max,
        initial_colors,
    )


def get_palette_stats(img_rgb):
    """
    Анализирует изображение и возвращает список словарей со статистикой цветов,
    отсортированный по убыванию частоты.
    """
    img_np = np.array(img_rgb)
    total_pixels = img_np.shape[0] * img_np.shape[1]
    
    # Извлекаем все пиксели и считаем уникальные цвета
    pixels = img_np.reshape(-1, 3)
    colors, counts = np.unique(pixels, axis=0, return_counts=True)
    
    # Сортируем по убыванию количества (от самых частых к редким)
    sort_indices = np.argsort(counts)[::-1]
    sorted_colors = colors[sort_indices]
    sorted_counts = counts[sort_indices]
    
    palette_data = []
    for i, (color, count) in enumerate(zip(sorted_colors, sorted_counts)):
        hex_code = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
        palette_data.append({
            "id": i + 1,
            "rgb": tuple(color),
            "hex": hex_code,
            "percentage": (count / total_pixels) * 100
        })

    return palette_data