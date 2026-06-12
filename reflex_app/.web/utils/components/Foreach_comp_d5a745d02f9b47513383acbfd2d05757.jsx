
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_d5a745d02f9b47513383acbfd2d05757 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.archived_cat_rows_rx_state_ ?? [],((row_rx_state_,index_caa5d9cbba1f42a8bb75c6f66e02da2a)=>(jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["background"] : "rgba(255,255,255,0.05)", ["border"] : "1px dashed rgba(255,255,255,0.08)", ["borderRadius"] : "8px", ["padding"] : "8px 12px", ["marginBottom"] : "5px", ["opacity"] : "0.7", ["alignItems"] : "center", ["width"] : "100%", ["gap"] : "8px" }),direction:"row",key:index_caa5d9cbba1f42a8bb75c6f66e02da2a,gap:"3"},jsx(RadixThemesBox,{css:({ ["width"] : "10px", ["height"] : "10px", ["borderRadius"] : "50%", ["background"] : row_rx_state_?.["color"], ["flexShrink"] : "0" })},),jsx(RadixThemesText,{as:"p",css:({ ["flex"] : "1", ["fontSize"] : "13px", ["color"] : "#606088", ["fontStyle"] : "italic" })},row_rx_state_?.["name"]),jsx(RadixThemesBox,{css:({ ["fontSize"] : "11px", ["color"] : "#30D158", ["cursor"] : "pointer", ["padding"] : "3px 8px", ["borderRadius"] : "4px", ["border"] : "1px solid #30D15844", ["&:hover"] : ({ ["background"] : "#30D15811" }), ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["flexShrink"] : "0" }),onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.unarchive_category", ({ ["cid"] : row_rx_state_?.["id"] }), ({  })))], [_e], ({  }))))},"Restore")))))
    )
});
