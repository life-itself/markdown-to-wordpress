<?php
// WordPress redirect rules for Life Itself migration
// Add this to your theme's functions.php or a custom plugin

function lifeitself_legacy_redirects() {
    \$redirects = array(
        '/manifesto' => '/blog/2015/11/01/manifesto',
        '/27aout' => '/blog/2022/07/15/art-eco-spirituality-aug-2022',
        '/sunflower-school' => '/blog/2021/11/12/sunflower-school-ecole-des-tournesols',
        '/mindfulness' => '/blog/2020/06/29/mindfulness-an-introduction',
        '/bergerac-build' => '/blog/2020/07/09/bergerac-build-festival-2020-gathering-builders-diggers-and-dreamers',
        '/imaginary-society' => '/blog/2020/08/18/the-imaginary-society-series',
        '/community-projects' => '/blog/2021/03/18/berlin-hub-community-projects',
        '/institute/compassionate-mental-health' => 'https://app-67d6f672c1ac1810207db362.closte.com/?p=869',
        '/deliberately-developmental-space' => '/blog/2021/10/05/deliberately-developmental-spaces-a-key-to-addressing-the-metacrisis',
        '/hangouts' => '/community',
        '/once-upon-a-time-series' => '/ordinary-people',
        '/tao/community-guidelines' => '/community',
        '/blog' => '/categories/all',
        '/ecosystem' => 'https://ecosystem.lifeitself.org',
        '/learn/culturology' => '/learn/cultural-evolution',
        '/programs' => '/residencies',
        '/qr' => 'https://app-67d6f672c1ac1810207db362.closte.com/?p=869',
        '/awakening-society' => '/learn/awakening-society',
        '/notes/wisdom-gap' => '/learn/wisdom-gap',
    );

    \$request_uri = \$_SERVER['REQUEST_URI'];
    if (isset(\$redirects[\$request_uri])) {
        wp_redirect(\$redirects[\$request_uri], 301);
        exit;
    }
}
add_action('init', 'lifeitself_legacy_redirects');
