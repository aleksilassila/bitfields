import RoundButton from "../components/RoundButton";

const Help = ({ visible, setVisible }) => {
	return (
		<div id="help">
			<div id="container">
				<button id="close" onClick={() => setVisible(false)}>
					x
				</button>
				<div id="divider">
					<div id="keybinds">
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
								<span>Fortify Boulder ($100): </span>
								<span>F</span>
							</li>
							<li>
								<span>Place Door ($300): </span>
								<span>G</span>
							</li>
						</ul>
					</div>
					<div id="titles">
						<h2>Titles</h2>
						<ul>
							<li>
								<span>#: Breakable wall</span>
							</li>
							<li>
								<span>O: Pickable boulder</span>
							</li>
							<li>
								<span>H: Ladder to underworld/overworld</span>
							</li>
							<li>
								<span>
									<span className="gold">M</span>: Geyser that
									can be collected for money. Colors indicate
									different amounts of money to be collected
								</span>
							</li>
							<li>
								<span>
									<span className="red">B</span>: Enemy bot
								</span>
							</li>
							<li>
								<span>
									<span className="red">@</span>: Enemy player
								</span>
							</li>
							<li>
								<span>
									D: Door that only the creator can enter
								</span>
							</li>
							<li>
								<span>█: Fortified boulder</span>
							</li>
						</ul>
					</div>
				</div>
				<h2>Overworld and Underworld</h2>
				<p>
					You can move between these levels using ladders (H). There's
					limited visibility and more bots in Underworld, which makes
					it a lot more dangerous place to roam in than Overworld.
					However, it's a great palce for a hideout or a base, for
					example. Just don't get lost down there!
				</p>
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

				#divider {
					display: flex;
					justify-content: space-around;
				}
			`}</style>
		</div>
	);
};

export default Help;
