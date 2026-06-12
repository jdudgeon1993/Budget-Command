
import {Fragment,memo,useContext,useEffect,useState} from "react"
import {ReflexEvent,applyEventActions,getBackendURL,isTrue,refs} from "$/utils/state"
import {EventLoopContext} from "$/utils/context"
import {WifiOff as LucideWifiOff} from "lucide-react"
import {jsx,keyframes} from "@emotion/react"
import env from "$/env.json"






export const DefaultOverlayComponents = memo(({}) => {
    
const [addEvents, connectErrors] = useContext(EventLoopContext);
const toast = refs['__toast'];
const toast_props = ({ ["description"] : ("Check if server is reachable at "+getBackendURL(env.EVENT).href), ["closeButton"] : true, ["duration"] : 120000, ["id"] : "websocket-error" });
const [userDismissed, setUserDismissed] = useState(false);
const [waitedForBackend, setWaitedForBackend] = useState(false);
(useEffect(
() => {
    if ((connectErrors.length >= 2)) {
        if (!userDismissed) {
            toast?.error(("Cannot connect to server: "+((connectErrors.length > 0) ? connectErrors[connectErrors.length - 1].message : '')+"."), {...toast_props, onDismiss: () => setUserDismissed(true)},)
        }
    } else {
        toast?.dismiss("websocket-error");
        setUserDismissed(false);  // after reconnection reset dismissed state
    }
}
, [connectErrors, waitedForBackend]))


    return(
        jsx(Fragment,{},jsx("div",{css:({ ["position"] : "fixed", ["width"] : "100vw", ["height"] : "0" }),title:("Connection Error: "+((connectErrors.length > 0) ? connectErrors[connectErrors.length - 1].message : ''))},jsx(Fragment,{},((connectErrors.length > 0)?(jsx(Fragment,{},jsx(LucideWifiOff,{css:({ ["color"] : "crimson", ["zIndex"] : 9999, ["position"] : "fixed", ["bottom"] : "33px", ["right"] : "33px", ["animation"] : (keyframes({ from: { opacity: 0 }, to: { opacity: 1 } })+" 1s infinite") }),size:32},))):(jsx(Fragment,{},))))),jsx(Fragment,{},))
    )
});
