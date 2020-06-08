import RoundButton from "../components/RoundButton";

const Help = ({ visible, setVisible }) => {
	return (
		<div id="help">
			<div id="container">
				<button id="close" onClick={() => setVisible(false)}>
					x
				</button>
				<h2>Keybinds</h2>
				<ul>
					<li>
						<span>Move: </span>
						<span>W, A, S, D</span>
					</li>
					<li>
						<span>Fine Movement (Move One Title): </span>
						<span>Arrow Keys</span>
					</li>
					<li>
						<span>Shoot: </span>
						<span>Space</span>
					</li>
					<li>
						<span>Mine / Collect / Break: </span>
						<span>E</span>
					</li>
					<li>
						<span>Fortify Boulder ($300): </span>
						<span>F</span>
					</li>
					<li>
						<span>Place Door ($1000): </span>
						<span>G</span>
					</li>
				</ul>
			</div>
			<style jsx>{`
				#help {
					display: ${visible ? "flex" : "none"};
					position: fixed;
					height: 100vh;
					width: 100vw;
					overflow: auto;
					align-items: stretch;
					align-content: stretch;
				}

				#container {
					margin: 8vh 8vw;
					padding: 2em;
					background-color: #000000aa;
					border-radius: 15px;
					box-sizing: border-box;
					flex-grow: 1;
					position: relative;
				}

				#close {
					position: absolute;
					top: 2rem;
					right: 2rem;

					color: #444444;
					text-shadow: none;
					background: none;
					border: none;
					font-size: 1.5em;
				}
			`}</style>
		</div>
	);
};

export default Help;
