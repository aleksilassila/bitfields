const Button = ({ value, className, ...rest }) => (
	<div className={className}>
		<input {...rest} className="button" type="button" value={value} />
		<style jsx>{`
			.button {
				font-family: "Roboto mono", monospace;

				border-radius: 2px;
				outline: none;
				background: none;

				cursor: pointer;

				color: lime;
				text-shadow: 0 0 3px lime;
				border: 2px solid #00ff00;
				box-shadow: 0 0 5px 0px lime;

				padding: 0.5rem 1rem;
			}
		`}</style>
	</div>
);

export default Button;
