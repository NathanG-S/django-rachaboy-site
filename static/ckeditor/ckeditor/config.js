/**
 * @license Copyright (c) 2003-2022, CKSource Holding sp. z o.o. All rights reserved.
 * For licensing, see https://ckeditor.com/legal/ckeditor-oss-license
 */

CKEDITOR.editorConfig = function( config ) {
	// Define changes to default configuration here. For example:
	// config.language = 'fr';
	// config.uiColor = '#AADC6E';
	
	config.allowedContent = {
		$1: {
			  elements: CKEDITOR.dtd,
			  attributes: true,
			  styles: true,
			  classes: true
			}
		};
	config.disallowedContent = '*[style]{*}'
	config.codeSnippet_theme = 'github';
};
//config.extraPlugins = 'myplugin,anotherplugin';
