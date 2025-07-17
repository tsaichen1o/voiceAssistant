import typography from '@tailwindcss/typography';

const config = {
	content: [
		"./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
		"./src/components/**/*.{js,ts,jsx,tsx,mdx}",
		"./src/app/**/*.{js,ts,jsx,tsx,mdx}",
	],
	theme: {
		extend: {
			keyframes: {
				blink: {
					"0%, 100%": { opacity: 1 },
					"50%": { opacity: 0 },
				},
				"fade-in": {
					from: { opacity: "0" },
					to: { opacity: "1" },
				},
				"pop-in": {
					"0%": {
						opacity: "0",
						transform: "scale(0.95) translateY(10px)",
					},
					"100%": {
						opacity: "1",
						transform: "scale(1) translateY(0)",
					},
				},
			},
			animation: {
				blink: "blink 1s step-end infinite",
				"fade-in": "fade-in 0.3s ease-out forwards",
				"pop-in": "pop-in 0.3s ease-out forwards",
			},
		},
	},
	plugins: [typography],
};

export default config