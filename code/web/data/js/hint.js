var authors = new Bloodhound({
  datumTokenizer: Bloodhound.tokenizers.whitespace,
  queryTokenizer: Bloodhound.tokenizers.whitespace,
  // url points to a json file that contains an array of country names, see
  // https://github.com/twitter/typeahead.js/blob/gh-pages/data/words.json
  prefetch: '/data/authors.json/'
});

var affiliations = new Bloodhound({
  datumTokenizer: Bloodhound.tokenizers.whitespace,
  queryTokenizer: Bloodhound.tokenizers.whitespace,
  // url points to a json file that contains an array of country names, see
  // https://github.com/twitter/typeahead.js/blob/gh-pages/data/words.json
  prefetch: '/data/affiliations.json/'
});


// passing in `null` for the `options` arguments will result in the default
// options being used
$('#authorform .typeahead').typeahead(null, {
  name: 'authors',
  source: authors,
  limit: 15
});

// passing in `null` for the `options` arguments will result in the default
// options being used
$('#affform .typeahead').typeahead(null, {
  name: 'affiliations',
  source: affiliations,
  limit: 10
});