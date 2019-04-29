<style type="text/css">img{max-width: 100%}</style>
<p>Simulated Annealing parameter changes.</p>
<?php

ini_set('display_startup_errors', 1);
ini_set('display_errors', 1);
error_reporting(-1);

$files = array();

foreach(glob('*.png') as $file) {
    $split = explode('-', str_replace('.out.csv.png', '', $file));
    if (!array_key_exists($split[0], $files)) {
        $files[$split[0]] = array();
    }
    $out = str_replace('.png', '', $file);
    $f = fopen($out, 'r');
    $score = intval(fgets($f));
    fclose($f);
    $files[$split[0]][] = array(
        'Tmin' => intval($split[1]),
        'Tmax' => intval($split[2]),
        'alpha' => floatval($split[3]),
        'iterations' => intval($split[4]),
        'img' => $file,
        'out' => $out,
        'score' => intval($score),
    );
}

function sort_entry($a, $b)
{
    return $a['score'] - $b['score'];
}

echo "<ul>\n";
foreach ($files as $inputset => $entries) {
    echo "\t<li><a href='#$inputset'>$inputset</a></li>\n";
}
echo "</ul>\n";

foreach ($files as $inputset => $entries) {
    echo "<h1 id='$inputset'>$inputset</h1>\n";
    usort($entries, "sort_entry");
    foreach ($entries as $entry) {
        $tmin = $entry['Tmin'];
        $tmax = $entry['Tmax'];
        $alpha = $entry['alpha'];
        $iterations = $entry['iterations'];
        $score = $entry['score'];
        $img = $entry['img'];
        echo "\t<h2>T=$tmin&rarr;$tmax &alpha;=$alpha N=$iterations</h2>\n";
        echo "\t\tScore: $score\n";
        echo "\t\t<img src='$img'/>\n";
    }
}
