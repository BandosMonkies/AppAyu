import React, { useEffect, useReducer, useRef, useState } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';
import {BrowserRouter,navLink,nav,Rout,Routers }
from react-router-DOM
// function App(){
//   const [inputValue, setInputValue] = useState("");
//   const count=useRef(0);
//   useEffect(()=>{
//     count.current=count.current+1
//   });
//   return (
//     <div>
//       <p>Type in the iput field</p>
//       <input type="text" value={inputValue} onChange={(e)=>setInputValue(e.target.value)}/>
//       <h1>Render count:{count.current}</h1>
      
//     </div>
//   );
// }



// function reducer(state,action){
//   switch(action.type){
//     case "i_age":
//       return {age: state.age+1};
//     case "iage":
//       return {age:state.age-1};
//     case "i__age":
//       return {age:state.age=0}
//       default:
//         return state;
//   }
// }
// function AgeCounter(){
//   const [state,dispatch]=useReducer(reducer,{age:42});
//   return (
//     <div>
//       <p>Age:{state.age}</p>
//       <button onClick={()=>dispatch({type:"i_age"})}>Increment Age</button>
//       <button onClick={()=>dispatch({type:"iage"})}>decrement</button>
//       <button onClick={()=>dispatch({type:"i__age"})}>reset</button>
//     </div>
//   );
// }
// function Myform(){
//   const [name,setName]=useState("");
//   return(
//     <form>
//       <label >

//         Enter your name:
//         <input type="text" value={name}
//         onChange={(e)=> setName(e.target.value)}
//         /></label>
//         <p>current value:{name}</p>
//     </form>
//   )
// }
function Home() {
  return(
    <P>hey budyy</P>
  );
  
}
function contacts() {
  return(
    <P>no contacts</P>
  );
  
}
function students() {
  return(
    <P>mai hu shravanakumar</P>
  );
  
}
function students_3rd() {
  return(
    <P>iam in third sem</P>
  )
  
}
function App(){
  return(
    <BrowserRouter>
    <nav>
      <navLink to="/">Home</navLink> <navLink to="/contacts">contacts</navLink> <navLink to="/students">students</navLink> <navLink to="/students_3rd">students_3rd</navLink>
    </nav>
    <Routers>
      <Rout path="/" element={<Home/>}/>
      <Rout path="/contacts" element={<contacts/>}/>
      <Rout path="/students" element={<students/>}/>
      <Rout path="/students_3rd" element={<students_3rd/>}/>
    </Routers>
    </BrowserRouter>
  );
}
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App/>);
export default App