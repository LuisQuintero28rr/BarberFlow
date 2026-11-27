(function () {

const style = document.createElement('style');

style.textContent = `

#bf-asistente-btn {

position: fixed;

bottom: 22px;

right: 22px;

width: auto;

padding: 12px 18px;

border-radius: 999px;

background: var(--accent-hover, #0284c7);

color: #ffffff;

border: 1px solid rgba(56, 189, 248, 0.4);

font-weight: 700;

font-size: 0.92rem;

cursor: pointer;

box-shadow: 0 10px 25px rgba(0, 0, 0, 0.45);

z-index: 9999;

margin: 0;

}

#bf-asistente-btn:hover {

background: #0369a1;

}

#bf-asistente-panel {

display: none;

position: fixed;

bottom: 82px;

right: 22px;

width: 350px;

max-width: calc(100vw - 32px);

max-height: 500px;

background: var(--card-bg, #1e293b);

border: 1px solid var(--border-color, #334155);

border-radius: 16px;

box-shadow: 0 18px 36px rgba(0, 0, 0, 0.55);

z-index: 9999;

flex-direction: column;

overflow: hidden;

}

#bf-asistente-panel.abierto {

display: flex;

}

.bf-header {

background: #0f172a;

padding: 14px 16px;

border-bottom: 1px solid var(--border-color, #334155);

display: flex;

justify-content: space-between;

align-items: center;

}

.bf-header strong {

color: var(--accent, #38bdf8);

font-size: 0.98rem;

}

.bf-header-acciones {

display: flex;

gap: 8px;

}

.bf-mini-btn {

width: auto;

margin: 0;

padding: 4px 9px;

font-size: 0.75rem;

border-radius: 6px;

background: #334155;

color: #f8fafc;

}

.bf-mensajes {

padding: 14px;

overflow-y: auto;

display: flex;

flex-direction: column;

gap: 10px;

flex: 1;

}

.bf-msg {

padding: 10px 12px;

border-radius: 10px;

font-size: 0.88rem;

line-height: 1.4;

white-space: pre-line;

}

.bf-msg.bot {

background: #0f172a;

color: #f8fafc;

border: 1px solid #334155;

align-self: flex-start;

}

.bf-msg.user {

background: var(--accent-hover, #0284c7);

color: #ffffff;

align-self: flex-end;

}

.bf-opciones {

padding: 10px 14px 14px;

border-top: 1px solid var(--border-color, #334155);

background: #0f172a;

display: flex;

flex-wrap: wrap;

gap: 8px;

}

.bf-opcion-btn {

width: auto;

flex: 1 1 calc(50% - 8px);

margin: 0;

padding: 9px 10px;

font-size: 0.82rem;

border-radius: 8px;

background: #1e293b;

color: #f8fafc;

border: 1px solid var(--accent, #38bdf8);

font-weight: 600;

}

.bf-opcion-btn:hover {

background: var(--accent-hover, #0284c7);

}

`;

document.head.appendChild(style);



const btnToggle = document.createElement('button');

btnToggle.id = 'bf-asistente-btn';

btnToggle.type = 'button';

btnToggle.textContent = '✨ Asistente IA';



const panel = document.createElement('div');

panel.id = 'bf-asistente-panel';

panel.innerHTML = `

<div class="bf-header">

<strong>✂️ Asistente de Estilo</strong>

<div class="bf-header-acciones">

<button type="button" class="bf-mini-btn" id="bf-reiniciar">Reiniciar</button>

<button type="button" class="bf-mini-btn" id="bf-cerrar">✕</button>

</div>

</div>

<div class="bf-mensajes" id="bf-mensajes"></div>

<div class="bf-opciones" id="bf-opciones"></div>

`;



document.body.appendChild(btnToggle);

document.body.appendChild(panel);



const mensajesEl = document.getElementById('bf-mensajes');

const opcionesEl = document.getElementById('bf-opciones');



let estado = {

categoria: null,

tipo_cabello: null,

largo_cabello: null,

estado_barba: null

};



function agregarMensaje(texto, autor = 'bot') {

const div = document.createElement('div');

div.className = `bf-msg ${autor}`;

div.textContent = texto;

mensajesEl.appendChild(div);

mensajesEl.scrollTop = mensajesEl.scrollHeight;

}



function establecerOpciones(lista) {

opcionesEl.innerHTML = '';

lista.forEach(item => {

const b = document.createElement('button');

b.type = 'button';

b.className = 'bf-opcion-btn';

b.textContent = item.label;

b.addEventListener('click', item.onClick);

opcionesEl.appendChild(b);

});

}



function iniciarFlujo() {

estado = { categoria: null, tipo_cabello: null, largo_cabello: null, estado_barba: null };

mensajesEl.innerHTML = '';

agregarMensaje('¿Cómo te puedo ayudar?');

establecerOpciones([

{ label: 'Corte de Cabello', onClick: () => elegirCategoria('cabello', 'Corte de Cabello') },

{ label: 'Corte de Barba', onClick: () => elegirCategoria('barba', 'Corte de Barba') }

]);

}



function elegirCategoria(cat, etiqueta) {

estado.categoria = cat;

agregarMensaje(etiqueta, 'user');



if (cat === 'cabello') {

agregarMensaje('¿Qué tipo de cabello tienes?');

const tipos = ['Lacio', 'Chino', 'Quebrado', 'Grueso', 'Delgado'];

establecerOpciones(tipos.map(t => ({

label: t,

onClick: () => elegirTipoCabello(t)

})));

} else {

agregarMensaje('¿Cómo es tu barba actualmente?');

const barbas = ['Abundante', 'Con huecos', 'Corta / Pocos días', 'Larga'];

establecerOpciones(barbas.map(b => ({

label: b,

onClick: () => consultarIA({ estado_barba: b }, b)

})));

}

}



function elegirTipoCabello(tipo) {

estado.tipo_cabello = tipo;

agregarMensaje(tipo, 'user');

agregarMensaje('¿De qué largo tienes tu cabello ahorita?');

establecerOpciones([

{ label: 'Corto', onClick: () => consultarIA({ largo_cabello: 'Corto' }, 'Corto') },

{ label: 'Largo', onClick: () => consultarIA({ largo_cabello: 'Largo' }, 'Largo') }

]);

}



async function consultarIA(parche, etiquetaUsuario) {

Object.assign(estado, parche);

agregarMensaje(etiquetaUsuario, 'user');

agregarMensaje('Analizando tu estilo con IA...');

establecerOpciones([]);



try {

const res = await fetch('/asistente-estilo', {

method: 'POST',

headers: { 'Content-Type': 'application/json' },

body: JSON.stringify(estado)

});

const data = await res.json();

mensajesEl.lastChild.remove();

agregarMensaje(data.respuesta || 'No pude generar una recomendación en este momento.');

} catch (e) {

mensajesEl.lastChild.remove();

agregarMensaje('Hubo un problema al consultar el asistente. Intenta de nuevo.');

}



establecerOpciones([

{ label: 'Consultar de nuevo', onClick: iniciarFlujo }

]);

}



btnToggle.addEventListener('click', () => {

panel.classList.toggle('abierto');

if (panel.classList.contains('abierto') && mensajesEl.children.length === 0) {

iniciarFlujo();

}

});



document.getElementById('bf-cerrar').addEventListener('click', () => {

panel.classList.remove('abierto');

});



document.getElementById('bf-reiniciar').addEventListener('click', iniciarFlujo);

})();